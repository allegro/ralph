(($, Foundation) ->
    'use strict';
    class AutocompleteWidget
        constructor: (widget, options) ->
            self = @
            self.$widget = $(widget)
            self.options =
                limit: 1
                interval: 500
                sentenceLength: 2
                watch: true

            self.options = $.extend self.options, options, self.$widget.data()
            self.$queryInput = $('.input', self.$widget);
            self.$status = $('.status', self.$widget);
            self.$suggestList = $('.suggest-list', self.$widget);
            self.$target = $(self.options.targetSelector);
            self.$currentItem = $('.item', self.$widget);
            self.$deleteButton = $('.delete', self.$currentItem);
            self.$noResults = $('.template.no-results', self.$suggestList);
            self.selectItem = -1;

            self.$deleteButton.on 'click', (e) -> self.deleteItem(e)
            self.$queryInput.on 'keydown', (e) -> self.keyDown(e)

            if self.options.watch
                Object.defineProperty document.querySelector(self.options.targetSelector), 'value', {
                    get: () ->
                        @getAttribute 'value'
                    set: (val) ->
                        self.changeTargetAfterPopup val
                        @setAttribute 'value', val
                    configurable: true
                }

        # keyDown: (event) ->
        #     self = @
        #     code = event.keyCode || event.which;
        #     # 40 key down in ASCII
        #     keyDown = 40
        #     # 38 key up in ASCII
        #     keyUp = 38;
        #     # 13 enter key in ASCII
        #     enterKey = 13;
        #     # [space] in ASCII
        #     startChar = 20
        #     # ~ in ASCII
        #     endChar = 126
        #     specialCodes = [
        #         8,
        #     ]

        #     $all_elements = $('li.item:not(.template, .no-results)', self.$widget)
        #     $all_elements.removeClass 'selected'

        #     if code == keyDown
        #         self.selectItem++
        #         if self.selectItem == $all_elements.length
        #             self.selectItem = 0

        #         $($all_elements[self.selectItem]).addClass 'selected'
        #         event.preventDefault();
        #         return
        #     if code == keyUp
        #         self.selectItem--
        #         if self.selectItem == -1
        #             self.selectItem = $all_elements.length - 1
        #         $($all_elements[self.selectItem]).addClass 'selected'
        #         event.preventDefault()
        #         return

        #     if code == enterKey
        #         self.itemClick
        #             target: $($all_elements[self.selectItem]).find('.link'),
        #             preventDefault: () ->
        #         event.preventDefault()
        #         return false

        #     if (code < startChar || code > endChar) && $.inArray(code, specialCodes) == -1
        #         return
        #     if self.timer
        #         clearTimeout self.timer
        #     self.timer = setTimeout () ->
        #         self.suggest()
        #     , self.options.interval
        #     return

        # getItemValue: (item) ->
        #     return item.label || item.__str__

        # stripHTMLTags: (value) ->
        #     div = document.createElement 'div'
        #     div.innerHTML = value;
        #     return div.textContent || div.innerText || ''

        # changeTargetAfterPopup: (val) ->
        #     self = @
        #     data = {}
        #     if self.notFromPopup
        #         self.notFromPopup = undefined
        #         return

        #     data[self.options.detailVar] = val
        #     self.fetch self.options.detailsUrl, data, (data) ->
        #         self.editMode false
        #         value = self.getItemValue data.results[0]
        #         $ '.title', self.$currentItem
        #             .html value
        #             .attr 'title', self.stripHTMLTags value
        #     return

        # editMode: (condition) ->
        #     self = @
        #     if condition
        #         this.clearSuggestList()
        #         this.$widget.addClass 'edit in-progress'
        #     else
        #         this.$widget.removeClass 'edit'
        #         this.$suggestList.hide()
        #     return

        # deleteItem: (event) ->
        #     self = @
        #     event.preventDefault()
        #     self.editMode(true)
        #     self.$queryInput.val('').focus()
        #     self.notFromPopup = true
        #     self.$target.val ''
        #     return

        # getQuery: () ->
        #     return this.$queryInput.val()

        # addItemToList: (item) ->
        #     self = @
        #     $template = $('.template.item', self.$suggestList)
        #     htmlItem = $template.clone().removeClass('template')
        #     $('.link', htmlItem).html(item.label || item.__str__).data('item', item)
        #     self.$suggestList.append(htmlItem)
        #     htmlItem.on 'mousemove', (event) ->
        #         li = $(event.target).closest('li')[0]
        #         self.selectItem = $('li:not(.template)', self.$suggestList).index(li)
        #     htmlItem.hover (event) ->
        #         $(this).addClass 'selected'
        #     , (event) ->
        #         $(this).removeClass 'selected'
        #     htmlItem.on 'click', (event) -> self.itemClick(event)
        #     return htmlItem

        # updateEditUrl: (editUrl) ->
        #     pencil = this.$widget.find('.change-related')
        #     pencil.attr 'href', editUrl
        #     if (editUrl)
        #         pencil.show()
        #     return

        # itemClick: (event) ->
        #     self = @
        #     event.preventDefault()
        #     $clickedItem = $(event.target).closest('.link')
        #     item = $clickedItem.data('item')
        #     $tooltip = $('.has-tip', this.$currentItem)
        #     value = self.getItemValue(item)
        #     $('.title', self.$currentItem).html(value).attr('title', self.stripHTMLTags(value))
        #     tip = Foundation.libs.tooltip.getTip($tooltip)
        #     if item.tooltip
        #         tip.html(item.tooltip)
        #     else
        #         tip.remove()

        #     self.notFromPopup = true
        #     old_val = self.$target.val()
        #     old_val = JSON.parse(old_val)
        #     old_val.push(item.pk)
        #     self.$target.val(JSON.stringify(old_val)).change()
        #     self.editMode(false)
        #     self.updateEditUrl(item.edit_url)

        # clearSuggestList: () ->
        #     this.$noResults.hide()
        #     this.$suggestList.hide()
        #     $('>:not(.template)', this.$suggestList).remove()

        # suggest: () ->
        #     self = @
        #     query = self.getQuery()
        #     self.clearSuggestList()
        #     if query.length < self.options.sentenceLength
        #         return false
        #     self.fetchItems(query, (data) ->
        #         if self.options.isEmpty
        #             self.addItemToList(
        #                 __str__: '&lt;empty&gt;',
        #                 pk: self.options.emptyValue
        #             )
        #         if data.results.length != 0
        #             $.each data.results, () ->
        #                 self.addItemToList(this)
        #         else
        #             self.$noResults.show()
        #         self.selectItem = -1
        #         self.$suggestList.show()
        #     )
        #     return

        # fetchItems: (query, callback) ->
        #     self = @
        #     data = {}
        #     data[this.options.queryVar] = query
        #     self.fetch(this.options.suggestUrl, data, callback)

        # fetch: (url, data, callback) ->
        #     self = @
        #     $failStatus = $('.fail', self.$status)
        #     $loader = $('.loader', self.$status)
        #     self.$widget.addClass('in-progress')
        #     $loader.show()
        #     $.ajax(
        #         url: url
        #         data: data || {}
        #     )
        #     .fail () ->
        #         $failStatus.show();
        #         Foundation.libs.tooltip.showTip($failStatus);
        #         setTimeout () ->
        #             Foundation.libs.tooltip.hide($failStatus);
        #         , 3000
        #     .always () ->
        #         $loader.hide()
        #         self.$widget.removeClass 'in-progress'
        #     .done callback

    # updateAfterClose = (id, newValue) ->
    #     $parent = $('#' + id).val(newValue);

    $.fn.extend autocomplete: (option) ->
        @each ->
          $this = $(this)
          data = $this.data('autocomplete')

          if !data
            $this.data 'autocomplete', (data = new AutocompleteWidget(this, option))
          if typeof option == 'string'
            data[option].apply(data, args)

    $('.autocomplete-widget').autocomplete()
) ralph.jQuery, Foundation
