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

    $(document).ready(function () {
        (new ScanResultsForm()).run();
    });
});

