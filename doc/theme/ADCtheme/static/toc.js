var TOC = {
    load: function () {
        $('#toc_button').click(TOC.toggle);
    },
    
    toggle: function () {
        if ($('#sphinxsidebar').toggle().is(':hidden')) {
            $('div.document').css('left', "0px");
            $('toc_button').removeClass("open");
        } else {
            $('div.document').css('left', "230px");
            $('#toc_button').addClass("open");
        }
        return $('#sphinxsidebar');
    }
};

$(document).ready(function () {
    TOC.load();
    $('#sphinxsidebar span.pre')
      .each(function(index) {
        var t = $(this);
        var html = t.html()
            .replace(/langacore\.kit\.django/ig, 'langacore&#46;kit&#46;django')
            .replace(/\.py$/ig, '&#46;py')
            .replace(/\.py(\W)/ig, '&#46;py\1')
            .replace(/\./ig, '.<br/>&nbsp;&nbsp;')
        t.html(html);    
        });
});
