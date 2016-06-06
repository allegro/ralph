(function($){
    $(function () {
        "use strict";
        $("div.select-other > select").change(function(){
            var $this = $(this), val = $this.val(), name = $this.attr('name');
            if(val === '__other__'){
                $this.after(
                    '<input class="vTextField" name="' + name + '__other__" type="text" autocomplete="off">'
                );
            }
            else {
                $this.parent().find(
                    'input[name="' + name + '__other__"]'
                ).remove();
            }
        });
    });

})(ralph.jQuery);
