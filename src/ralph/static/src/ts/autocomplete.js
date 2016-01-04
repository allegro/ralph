/// <reference path="jquery.d.ts" />
/// <reference path="foundation.d.ts" />
(function ($, Foundation) {
    var AutocompleteWidget = (function () {
        function AutocompleteWidget(widget, options) {
            this.$widget = $(widget);
            this.options = {
                limit: 1,
                interval: 500,
                sentenceLength: 2,
                watch: true
            };
            this.options = $.extend(this.options, options, this.$widget.data());
        }
        return AutocompleteWidget;
    })();
})(jQuery, Foundation);
