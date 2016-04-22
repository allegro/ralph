// Fill fields in bulk edit and split asset forms
(function($) {
    $(function () {
        "use strict";
        // We use absolute positioning for toolbar therefore body must be relative
        $('body').css('position', 'relative');
        // Disable autocomplete without cluttering html attributes
        $('input').attr('autocomplete', 'off');

        var $fill_elements = $(
            'input[type=text]:not(.no-fillable), select, textarea, input[type=number]:not(.no-fillable), auto-complete:not(.no-fillable)',
            $('.bulk-edit.result-list')
        );

        var toggle_toolbar = function(element) {
            var $parent = element.closest('td');
            var $toolbar = $parent.find('.float_toolbar');
            if ($toolbar.length === 0) {
                var parent_height = $parent.height();
                $toolbar = $('#float_toolbar').clone();
                $toolbar.removeAttr('id');
                if (element[0].tagName === 'AUTO-COMPLETE') {
                    $toolbar.data(
                        'input_id',
                        $parent.find('auto-complete')[0].id
                    );
                } else {
                    var $input = $parent.find('input, select, textarea');
                    $toolbar.data('input_id', $input[0].id);
                }
                $parent.append($toolbar);
                $parent.css('position', 'relative');
                $toolbar.css('top', parent_height / 2 - 12 + 'px');

                $toolbar.on('click', function(event) {
                    event.preventDefault();
                    var input_id = $(this).data('input_id');
                    var matcher = /(.*)-([0-9]+)-(.*)/;
                    var results = matcher.exec(input_id);
                    if (results) {
                        var $fields = $('[id^=' + results[1] + '-][id$=-' + results[3] + ']');
                        var value = $('#' + input_id).val();
                        $fields.val(value);
                        $fields.closest('td').addClass('fill-changed');
                        $fields.closest('td').animate({backgroundColor: 'white'});
                    }
                });
                $toolbar.show();
            }
        };

        $fill_elements.each(function(i, element) {
            toggle_toolbar($(element));
        });
    });
})(ralph.jQuery);
