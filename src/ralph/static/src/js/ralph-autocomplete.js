(function($, Foundation) {
    'use strict';
    var AutocompleteWidget = function(widget, options) {
        this.$widget = $(widget);
        this.options = {
            interval: 500,
            sentenceLength: 3,
            watch: true
        };
        this.options = $.extend(this.options, options, this.$widget.data());
        this.$queryInput = $('.input', this.$widget);
        this.$status = $('.status', this.$widget);
        this.$suggestList = $('.suggest-list', this.$widget);
        this.$target = $(this.options.targetSelector, this.$widget);
        this.$currentItem = $('.item', this.$widget);
        this.$deleteButton = $('.delete', this.$currentItem);
        this.$noResults = $('.template.no-results', this.$suggestList);

        var that = this;
        this.$deleteButton.on('click', function(e) {that.deleteItem(e);});
        this.$queryInput.on('keydown', function(e) {that.keyDown(e);});

        if(this.options.watch) {
            Object.defineProperty(document.querySelector(that.options.targetSelector), 'value', {
                get: function(){
                    return this.getAttribute('value');
                },
                set: function(val) {
                    that.changeTargetAfterPopup(val);
                    this.setAttribute('value', val);
                }
            });
        }
    };
    AutocompleteWidget.prototype.keyDown = function(event) {
        var that = this;
        var code = event.keyCode || event.which;
        var startChar = 20; // [space] in ASCII
        var endChar = 126; // ~ in ASCII
        var specialCodes = [
            8, // backspace
        ];
        if (
            (code < startChar || code > endChar) &&
            $.inArray(code, specialCodes) === -1
        ) {
            return;
        }
        if(that.timer) {
            clearTimeout(that.timer);
        }
        that.timer = setTimeout(function() {
            that.suggest();
        }, that.options.interval);
    };
    AutocompleteWidget.prototype.changeTargetAfterPopup = function(val) {
        var that = this;
        if (that.notFromPopup) {
            that.notFromPopup = undefined;
            return;
        }
        var data = {};
        data[that.options.detailVar] = val;
        that.fetch(that.options.detailsUrl, data, function(data) {
            that.editMode(false);
            $('.title', that.$currentItem).html(data.results[0].__str__);
        });

    };
    AutocompleteWidget.prototype.editMode = function(on) {
        if (on) {
            this.clearSuggestList();
            this.$widget.addClass('edit in-progress');
        }
        else {
            this.$widget.removeClass('edit');
            this.$suggestList.hide();
        }
    };
    AutocompleteWidget.prototype.deleteItem = function(event) {
        event.preventDefault();
        this.editMode(true);
        this.$queryInput.val('').focus();
        this.notFromPopup = true;
        this.$target.val('');
    };
    AutocompleteWidget.prototype.getQuery = function() {
        return this.$queryInput.val();
    };
    AutocompleteWidget.prototype.addItemToList = function(item) {
        var that = this;
        var $template = $('.template.item', that.$suggestList);
        var htmlItem = $template.clone().removeClass('template');
        $('.link', htmlItem).html(item.__str__).data('item', item);
        that.$suggestList.append(htmlItem);
        htmlItem.on('click', function(event){that.itemClick(event);});
        return htmlItem;
    };
    AutocompleteWidget.prototype.updateEditUrl = function(editUrl) {
        var pencil = this.$widget.find('.change-related');
        pencil.attr('href', editUrl);
        if(editUrl) {
            pencil.show();
        }
    };
    AutocompleteWidget.prototype.itemClick = function(event) {
        event.preventDefault();
        var $clickedItem = $(event.target);
        var item = $clickedItem.data('item');
        $('.title', this.$currentItem).html(item.__str__);
        this.notFromPopup = true;
        this.$target.val(item.pk);
        this.editMode(false);
        this.updateEditUrl(item.edit_url);
    };
    AutocompleteWidget.prototype.clearSuggestList = function() {
        this.$noResults.hide();
        this.$suggestList.hide();
        $('>:not(.template)', this.$suggestList).remove();
    };
    AutocompleteWidget.prototype.suggest = function() {
        var that = this;
        var query = that.getQuery();
        that.clearSuggestList();
        if (query.length < that.options.sentenceLength) {
            return false;
        }
        that.fetchItems(query, function(data) {
            if (data.results.length !== 0) {
                $.each(data.results, function() {
                    that.addItemToList(this);
                });
            }
            else {
                that.$noResults.show();
            }
            that.$suggestList.show();
        });
    };
    AutocompleteWidget.prototype.fetchItems = function(query, callback) {
        var data = {};
        data[this.options.queryVar] = query;
        this.fetch(this.options.suggestUrl, data, callback);
    };
    AutocompleteWidget.prototype.fetch = function(url, data, callback) {
        var that = this;
        var $failStatus = $('.fail', this.$status);
        var $loader = $('.loader', this.$status);

        that.$widget.addClass('in-progress');
        $loader.show();
        $.ajax({
            url: url,
            data: data || {},
        })
            .fail(function() {
                $failStatus.show();
                Foundation.libs.tooltip.showTip($failStatus);
                setTimeout(function() {
                    Foundation.libs.tooltip.hide($failStatus);
                }, 3000);
            })
            .always(function() {
                $loader.hide();
                that.$widget.removeClass('in-progress');
            })
            .done(callback);
    };
    $.fn.autocomplete = function(options) {
        return this.each(function() {
            $.data(this, 'autocomplete', new AutocompleteWidget(this, options));
        });
    };
})(jQuery, Foundation);

(function($) {
    function updateAfterClose(id, newValue) {
        var $parent = $('#' + id).val(newValue);
    }
    $('.autocomplete-widget').autocomplete();
}(jQuery));
