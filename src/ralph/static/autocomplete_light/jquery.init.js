var yl = yl || ralph;


;(function ($) {
    $('select').on('select2:select', function(evt){
        $.get(
            $(evt.target).data('autocompleteLightUrl'),
            {'id': evt.params.data.id, 'selected': true}
        );
    });
})(yl.jQuery);
