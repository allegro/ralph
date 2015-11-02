// Fill fields in bulk edit and split asset forms
$(function () {
    "use strict";
    // We use absolute positioning for toolbar therefore body must be relative
    $('body').css('position', 'relative');
    // Disable autocomplete without cluttering html attributes
    $('input').attr('autocomplete', 'off');

    $('.bulk-edit input[type=text]:not(.no-fillable), .bulk-editt select, .autocomplete-widget').blur(function() {
        $('#float_toolbar').hide();
    });

    var toggle_toolbar = function(element) {
        var $toolbar = $('#float_toolbar');
        var result_list_offset = $('#bulk-edit-result').offset();
        var input_offset = $(element).offset();
        var width = element.clientWidth;
        var distance_top = input_offset.top - result_list_offset.top;
        var distance_left = -18;
        var element_id = element.id;

        if ($(element).hasClass('autocomplete-widget')) {
            element_id = $(element).data('target-selector').substr(1);
        }

        $toolbar.data('input_id', element_id);
        $toolbar.css('left', parseInt(input_offset.left) + width + distance_left + 'px');
        $toolbar.css('top', distance_top + 'px');
        $toolbar.show();
    };

    $('.bulk-edit input[type=text]:not(.no-fillable), .bulk-edit select, .autocomplete-widget').mouseover(function() {
        toggle_toolbar(this);
    });

    /*
     * Mousedown because as we use the "blur" in #float_toolbar
     * "click" does not work
     */
    $('#float_toolbar').mousedown(function() {
        var input_id = $(this).data('input_id');
        var from = $(this).data('from');
        var matcher = /(.*)-([0-9]+)-(.*)/;
        var results = matcher.exec(input_id);
        var $fields = $('[id^=' + results[1] + '-][id$=-' + results[3] + ']');
        var value = $('#' + input_id).val();
        if (value) {
            $fields.val(value);
            $fields.closest('td').addClass('fill-changed');
            $fields.closest('td').animate({backgroundColor: 'white'});
        }

        $(this).hide();
        return false;
    });
});
