/// <reference path="jquery.d.ts" />
/// <reference path="foundation.d.ts" />

(function($, Foundation) {
    interface AutocompleteConfig {
        limit: number;
        interval: number;
        sentenceLength: number;
        watch: boolean;
        targetSelector?: string;
        detailVar?: string;
        detailsUrl?: string;
        suggestUrl?: string;
        queryVar?: string;
        isEmpty?: boolean;
        emptyValue?: string;
    }

    interface AutocompleteItem {
        __str__: string;
        label?: string;
        pk?: string;
    }

    class AutocompleteWidget {
        private selectItem: number;
        private $widget: JQuery;
        private $queryInput: JQuery;
        private $status: JQuery;
        private $suggestList: JQuery;
        private $target: JQuery;
        private config: AutocompleteConfig;
        private $currentItem: JQuery;
        private $deleteButton: JQuery;
        private $noResults: JQuery;
        private timer: number;
        private notFromPopup: boolean;

        constructor(widget: HTMLElement, config: AutocompleteConfig) {
            this.$widget = $(widget);
            this.notFromPopup = true;
            this.config = {
                limit: 1,
                interval: 500,
                sentenceLength: 2,
                watch: true,
            };
            this.config = $.extend(this.config, config, this.$widget.data());
            this.$queryInput = $('.input', this.$widget);
            this.$status = $('.status', this.$widget);
            this.$suggestList = $('.suggest-list', this.$widget);
            this.$target = $(this.config.targetSelector);
            this.$currentItem = $('.item', this.$widget);
            this.$deleteButton = $('.delete', this.$currentItem);
            this.$noResults = $('.template.no-results', this.$suggestList);
            this.selectItem = -1;

            this.$deleteButton.on('click',(e: Event) => this.deleteItem(e));
            this.$queryInput.on('keydown', (e: KeyboardEvent) => this.keyDown(e));

            // TODO: scopes
            var outer_this = this;
            if(this.config.watch) {
                Object.defineProperty(document.querySelector(this.config.targetSelector), 'value', {
                    get: function() {
                        this.getAttribute('value');
                    },
                    set: function(val) {
                        outer_this.changeTargetAfterPopup(val);
                        this.setAttribute('value', val)
                    },
                    configurable: true
                })
            };
        }

        keyDown(event: KeyboardEvent) {
            let code = event.keyCode || event.which;
            // 40 key down in ASCII
            var keyDown = 40
            // 38 key up in ASCII
            var keyUp = 38;
            // 13 enter key in ASCII
            var enterKey = 13;
            // [space] in ASCII
            var startChar = 20
            // ~ in ASCII
            var endChar = 126
            var specialCodes = [
                8,
            ]

            var $all_elements = $('li.item:not(.template, .no-results)', this.$widget);
            $all_elements.removeClass('selected');

            if (code == keyDown) {
                this.selectItem++;
                if (this.selectItem == $all_elements.length) {
                    this.selectItem = 0;
                }
                $($all_elements[this.selectItem]).addClass('selected');
                event.preventDefault();
                return
            }

            if (code == keyUp) {
                this.selectItem--;
                if (this.selectItem == -1) {
                    this.selectItem = $all_elements.length - 1;
                }
                $($all_elements[this.selectItem]).addClass('selected');
                event.preventDefault()
                return;
            }
            if (code == enterKey) {
                this.itemClick({
                    target: $($all_elements[this.selectItem]).find('.link'),
                        preventDefault: () => event.preventDefault()
                })
                return false;
            }
            if ((code < startChar || code > endChar) && $.inArray(code, specialCodes) == -1)
                return
            if (this.timer) {
                clearTimeout(this.timer);
            }
            this.timer = setTimeout(() => this.suggest(), this.config.interval);
            return;
        }

        getItemValue(item: AutocompleteItem) {
            return item.label || item.__str__
        }

        stripHTMLTags(value: string) {
            let div = document.createElement('div');
            div.innerHTML = value;
            return div.textContent || div.innerText || '';
        }

        changeTargetAfterPopup(val){
            var data = {};
            if (this.notFromPopup) {
                this.notFromPopup = false;
                return
            }
            data[this.config.detailVar] = val;
            this.fetch(this.config.detailsUrl, data, (response_data: any) => {
                this.editMode(false);
                var value = this.getItemValue(data['results'][0]);
                $('.title', this.$currentItem).html(value).attr('title', this.stripHTMLTags(value));
            });
        }

        editMode(condition: boolean) {
            if (condition) {
                this.clearSuggestList();
                this.$widget.addClass('edit-in-progress');
            }
            else {
                this.$widget.removeClass('edit');
                this.$suggestList.hide();
            }
        }

        deleteItem(event: Event) {
            event.preventDefault();
            this.editMode(false);
            this.$queryInput.val('').focus();
            this.notFromPopup = true;
            this.$target.val('');
        }

        getQuery() {
            return this.$queryInput.val();
        }

        addItemToList(item: AutocompleteItem) {
            var $template = $('.template.item', this.$suggestList);
            var htmlItem = $template.clone().removeClass('template');
            $('.link', htmlItem).html(item.label || item.__str__).data('item', item)
            this.$suggestList.append(htmlItem);
            htmlItem.on('mousemove', (event) => {
                var li = $(event.target).closest('li')[0]
                this.selectItem = $('li:not(.template)', this.$suggestList).index(li)
            });
            htmlItem.hover(
                (event) => $(this).addClass('selected'),
                (event) => $(this).removeClass('selected')
            );
            htmlItem.on('click', (event: Event) => {this.itemClick(event) });
            console.log(item)
            return htmlItem;
        }

        updateEditUrl(editUrl: string) {
            var pencil = this.$widget.find('.change-related')
            pencil.attr('href', editUrl)
            if (editUrl)
                pencil.show()
        }

        // TODO: Event instead of any
        itemClick(event: any) {
            event.preventDefault();
            var $clickedItem = $(event.target).closest('.link');
            var item = $clickedItem.data('item');
            var $tooltip = $('.has-tip', this.$currentItem);
            var value = this.getItemValue(item);
            $('.title', this.$currentItem).html(value).attr('title', this.stripHTMLTags(value));
            var tip = Foundation.libs.tooltip.getTip($tooltip)
            if (item.tooltip) {
                tip.html(item.tooltip);
            }
            else {
                tip.remove();
            }

            this.notFromPopup = true;
            var old_val = this.$target.val() || '[]'
            old_val = JSON.parse(old_val)
            old_val.push(item.pk)
            this.$target.val(JSON.stringify(old_val)).change()
            this.editMode(false)
            this.updateEditUrl(item.edit_url);
        }

        clearSuggestList() {
            this.$noResults.hide();
            this.$suggestList.hide();
            $('>:not(.template)', this.$suggestList).remove();
        }

        fetchItems(query: string, callback: Function){
            var data = {};
            data[this.config.queryVar] = query
            this.fetch(this.config.suggestUrl, data, callback)
        }

        fetch(url: string, data: any, callback: Function) {
            var $failStatus = $('.fail', this.$status)
            var $loader = $('.loader', this.$status)
            this.$widget.addClass('in-progress')
            $loader.show();
            $.ajax({
                url: url,
                data: data || {}
            })
                .fail(() => {
                    $failStatus.show();
                    Foundation.libs.tooltip.showTip($failStatus);
                    setTimeout(
                        () => Foundation.libs.tooltip.hide($failStatus),
                        3000
                    );
                })
                .always(() => {
                    $loader.hide()
                    this.$widget.removeClass('in-progress');
                })
                .done(callback);
        }

        suggest() {
            var query = this.getQuery();
            this.clearSuggestList();
            if (query.length < this.config.sentenceLength)
                return false
            this.fetchItems(query, (data) => {
                if (this.config.isEmpty) {
                    this.addItemToList({
                        __str__: '&lt;empty&gt;',
                        pk: this.config.emptyValue
                    })
                }
                if (data.results.length != 0) {
                    // TODO: fixme
                    $.each(data.results, (idx, element) => {
                        this.addItemToList(element);
                    });

                }
                else
                    this.$noResults.show()
                    this.selectItem = -1
                    this.$suggestList.show()
            });
        }
    }

    $.fn.extend({
        autocomplete: function(config) {
            this.each(function() {
                let $this = $(this);
                let data = $this.data('autocomplete');
                if (!data) {
                    data = new AutocompleteWidget(this, config);
                    $this.data('autocomplete', data);
                }
            });
        }
    });
    $('.autocomplete-widget').autocomplete();
})(jQuery, Foundation)

