define(['jquery'], function ($) {
    function initialize() {
        $("li.menu-item-ralph-cli").click(function() {
            $('.beast-info-modal').modal();
        });
        $("div.quickscan input.search-query").blur(function() {
            $('.quickscan').hide();
        });
        $("li.menu-item-quick-scan").click(function() {
            $('div.quickscan').css('left', $(this).offset().left + "px");
            $('div.quickscan').css('top', $(this).offset().top + 32 + "px");
            $('div.quickscan').show();
            $('div.quickscan input').focus();
        });
    }

    return {
        initialize: initialize
    };
});
