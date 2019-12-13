(function ($) {
    'use strict';
    $('.datepicker').fdatepicker({format: 'yyyy-mm-dd'});
    $('.datepicker-with-time').fdatepicker({
        format: 'yyyy-mm-dd hh:ii:ss',
        disableDblClickSelection: true,
        pickTime: true
    });
}(ralph.jQuery));
