// Fill fields in bulk edit and split asset forms
(function($) {
    $(function () {
        "use strict";
        // We use absolute positioning for toolbar therefore body must be relative
        $('body').css('position', 'relative');
        // Disable autocomplete without cluttering html attributes
        $('input').attr('autocomplete', 'off');

        var $fill_elements = $('.bulk-edit input[type=text]:not(.no-fillable), .bulk-edit select, .bulk-edit textarea, .bulk-edit .autocomplete-widget');
        $fill_elements.blur(function() {
            $('#float_toolbar').hide();
        });

        var toggle_toolbar = function(element, action) {
            var $parent = element.closest('td');
            var $toolbar = $parent.find('.float_toolbar');
            if ($toolbar.length === 0) {
                var parent_height = $parent.height();
                $toolbar = $('#float_toolbar').clone();
                $toolbar.removeAttr('id');
                if ($(element).hasClass('autocomplete-widget')) {
                    $toolbar.data(
                        'input_id',
                        $(element).data('target-selector').substr(1)
                    );
                } else {
                    var $input = $parent.find('input, select, textarea');
                    $toolbar.data('input_id', $input[0].id);
                }
                $parent.append($toolbar);
                $parent.css('position', 'relative');
                $toolbar.css('top', parent_height / 2 - 12 + 'px');

                $toolbar.on('click', function() {
                    var input_id = $(this).data('input_id');
                    var from = $(this).data('from');
                    var matcher = /(.*)-([0-9]+)-(.*)/;
                    var results = matcher.exec(input_id);
                    if (results) {
                        var $fields = $('[id^=' + results[1] + '-][id$=-' + results[3] + ']');
                        var value = $('#' + input_id).val();
                        if (value) {
                            $fields.val(value);
                            $fields.closest('td').addClass('fill-changed');
                            $fields.closest('td').animate({backgroundColor: 'white'});
                        }
                    }
                    return false;
                });
            }

            if (action == 'show') {
                $toolbar.show();
            } else {
                $toolbar.hide();
            }
        };

        $fill_elements.each(function(i, element) {
            $(element).parent().mouseenter(function() {
                toggle_toolbar($(element), 'show');
            }).mouseleave(function() {
                toggle_toolbar($(element), 'hide');
            });
        });
    });
})(ralph.jQuery);
