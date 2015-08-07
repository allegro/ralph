// Fill fields in bulk edit and split asset forms
$(function () {
    "use strict";
    // We use absolute positioning for toolbar therefore body must be relative
    $('body').css('position', 'relative');
    // Disable autocomplete without cluttering html attributes
    $('input').attr('autocomplete', 'off');

    $('.result-list input[type=text]:not(.no-fillable), .result-list select').blur(function() {
        $('#float_toolbar').hide();
    });

    var toggle_toolbar = function(input) {
        var $toolbar = $('#float_toolbar');
        var offset = $(input).offset();
        var width = input.clientWidth;
        var distance_left = -30;
        var distance_top = -134;

        $toolbar.data('input_id', input.id);
        $toolbar.css('left', parseInt(offset.left) + width + distance_left + 'px');
        $toolbar.css('top', parseInt(offset.top) + distance_top + 'px');
        $toolbar.show();
    };

    $('.result-list input[type=text]:not(.no-fillable), .result-list select').focus(function() {
        toggle_toolbar(this);
    });

    /*
     * Mousedown because as we use the "blur" in #float_toolbar
     * "click" does not work
     */
    $('#float_toolbar').mousedown(function() {
        var input_id = $(this).data('input_id');
        var matcher = /(.*)-([0-9]+)-(.*)/;
        var results = matcher.exec(input_id);
        var $fields = $('[id^=' + results[1] + '-][id$=-' + results[3] + ']');

        $fields.val($('#' + input_id).val());
        $fields.parent().addClass('fill-changed');
        $fields.parent().animate({backgroundColor: 'white'});

        $(this).hide();
        return false;
    });
});
