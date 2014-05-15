require(['jquery'], function ($) {
    'use strict';

    var ScanResultsForm = function () {};

    ScanResultsForm.prototype.handleShowDiffButtons = function () {
        $('[data-role="show_diff_btn"]').click(function () {
            var container = $(this).parents(
                '[data-role="diff_select_widget"]'
            ).find(
                '[data-role="diff_details"]'
            );
            if ($(this).hasClass('active')) {
                $(container).hide();
            } else {
                $(container).show();
            }
        });
    };

    ScanResultsForm.prototype.handleShowAdvancedModeButtons = function () {
        $('[data-role="show_advanced_mode_btn"]').click(function () {
            var mainFields = $(this).parents(
                '[data-role="diff_select_widget"]'
            ).find(
                '[data-role="advanced_mode"]'
            );
            var customFields = $(this).parents(
                '[data-role="controls_wrapper"]'
            ).find(
                '[data-role="custom_control_wrapper"]'
            );
            if ($(this).hasClass('active')) {
                $(mainFields).hide();
                $(customFields).hide();
            } else {
                $(mainFields).show();
                $(customFields).show();
            }
        });
    };

    ScanResultsForm.prototype.run = function () {
        this.handleShowDiffButtons();
        this.handleShowAdvancedModeButtons();
    };

    var ScanSelectPluginsForm = function () {};

    ScanSelectPluginsForm.prototype.handleSelectAllButton = function () {
        var formContainer = $('[data-role="select-plugins-form"]');

        var selectAll = function() {
            $(formContainer).find(':checkbox').prop('checked', true);
        };

        var unselectAll = function () {
            $(formContainer).find(':checkbox').prop('checked', false);
        };

        $('[data-role="select-all-btn"]').click(function () {
            if ($(this).hasClass('active')) {
                unselectAll();
            } else {
                selectAll();
            }
        });
    };

    ScanSelectPluginsForm.prototype.run = function () {
        this.handleSelectAllButton();
        $('[data-role="select-all-btn"]').click();
        $('button[type=submit]#upper-submit').first().focus();
    };

    $(document).ready(function () {
        (new ScanResultsForm()).run();
        (new ScanSelectPluginsForm()).run();
    });
});

