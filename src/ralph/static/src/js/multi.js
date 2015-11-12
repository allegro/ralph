(function($){
    'use strict';
    var PermissionWidget = function(accordion) {
        this.accordion = $(accordion);
        this.input = $('#id_' + this.accordion.data('multi'));
        this.checkboxSelector = 'input[type=checkbox]';
        this.selectAllSelector = 'input[type=checkbox].select-all';
        this.register(this.checkboxSelector);
        this.classExpand = 'action-expand';
        this.classCollapse = 'action-collapse';
    };

    PermissionWidget.prototype.register = function(target) {
        var that = this;

        $(this.accordion).siblings('.expand')
            .click(function() {
                var $this = $(this);
                if ($this.hasClass('action-expand')) {
                    $('li, .content', that.accordion).addClass('active');
                    $this.html('Collapse all')
                         .addClass(that.classCollapse)
                         .removeClass(that.classExpand);
                }
                else {
                    $('li, .content', that.accordion).removeClass('active');
                    $this.html('Expand all')
                         .addClass(that.classExpand)
                         .removeClass(that.classCollapse);
                }
            });

        $(target)
            .parents('.accordion-navigation')
            .each(function(idx, section) {
                that.refreshSection(section);
                that.registerSelectAllCheckbox(section);
            });

        $(target, that.accordion).not(that.selectAllSelector).click(function() {
            $(this).parents('.accordion-navigation')
                   .each(function(idx, section) {
                       that.refreshSection(section);
                   });
        });

        $(target, that.accordion).click(function() {
            that.refreshInput();
        });
    };

    PermissionWidget.prototype.registerSelectAllCheckbox = function(section) {
        var that = this;
        $(that.selectAllSelector, section).click(function() {
            var checked = $(this).is(':checked');
            var checkboxes = $(that.checkboxSelector, section).not(that.selectAllSelector);
            checkboxes.prop('checked', checked);
            that.refreshSection(section);
        });
    };

    PermissionWidget.prototype.refreshInput = function() {
        var that = this;
        var values = [];
        $(that.checkboxSelector + ':checked', that.accordion).not(that.selectAllSelector).each(function() {
            values.push($(this).val());
        });
        that.input.val(values);
    };

    PermissionWidget.prototype.refreshSection = function(section) {
        var that = this;
        var allCheckboxes = $(this.checkboxSelector, section).not(that.selectAllSelector);
        var checked = $(this.checkboxSelector + ':checked', section).not(that.selectAllSelector);
        var allCheckbox = $(that.selectAllSelector, section);
        allCheckbox.prop('checked', allCheckboxes.length === checked.length);
        this.setCounter(section, checked.length);
    };

    PermissionWidget.prototype.setCounter = function(element, value) {
        var $counter = $('.counter', element);
        $counter.html(value);
    };

    $(document).ready(function() {
        $.each($('.accordion[data-multi]'), function(index, value) {
            new PermissionWidget(value);
        });
    });
})(ralph.jQuery);
