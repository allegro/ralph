$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});


$(function ($) {
    /* Some buttons may require confirmation. */
    $('button.[data-confirm]').click(function () {
        var confirm_dialog = $(this).attr('data-confirm');
        $(confirm_dialog).modal('show');
        /* The actual button should be repeated in the modal dialog. */
        return false;
    });
    /* Clearing the "manual field" status. */
    $('a[data-clear-field]').click(function () {
        var field_name = $(this).attr('data-clear-field');
        var device_id = $(this).attr('data-device-id');
        var button = $(this);
        $.post('/ui/unlock-field/', {
            device: device_id,
            field: field_name
        }, function (data) {
            button.fadeOut();
            button.closest('.control-group').removeClass('warning');
        }, 'json');
    });
    $('div.add-popover[').popover({
        placement: 'left'
    });
    $('a[rel="tooltip"]').tooltip();
    $('input[title]').tooltip();
    $('.select-all').click(function () {
        $('input[name="select"]').prop('checked', true);
        $('input[name="items"]').prop('checked', true);
    });
    $('.select-pages').click(function () {
        $('input[name="select"]').prop('checked', true);
        $('input[name="selectall"]').prop('checked', true);
    });
    $('.select-none').click(function () {
        $('input[name="select"]').prop('checked', false);
        $('input[name="items"]').prop('checked', false);
        $('input[name="selectall"]').prop('checked', false);
    });
    $('.select-toggle').click(function() {
        $('input[name="select"]').each(function () {
            this.checked = !this.checked;
        });
        $('input[name="items"]').each(function () {
            this.checked = !this.checked;
        });
        $('input[name="selectall"]').prop('checked', false);
    });
    $('form.bulk-edit-form input').not('.add-on *').change(function () {
        $(this).parent('.input-prepend').find('.add-on input').prop('checked', true);
    });
    $('form.bulk-edit-form select').not('.add-on *').change(function () {
        $(this).parent('.input-prepend').find('.add-on input').prop('checked', true);
    });
    $('form.bulk-edit-form textarea').not('.add-on *').change(function () {
        $(this).parent('.input-prepend').find('.add-on input').prop('checked', true);
    });
    $('form.bulk-edit-form .warning input').not('.add-on *').attr('placeholder', 'Different values...');


    $('form#disco-form').submit(function () {
        var $form = $(this);
        var $console = $('#disco-console')
        var $button = $form.find('button')
        var interval = null;
        $form.find('button, input').addClass('disabled').attr('disabled', '');
        $button.find('i').addClass('loading')
        $console.addClass('loading')
        var request = $.ajax({
            type: 'POST',
            url: '/ui/discover/',
            data: 'ip=' + $form.find('input[name="ip"]').val(),
            timeout: 600000,
            success: function (data, textStatus, request) {
                $form.find('button, input').removeClass('disabled').attr('disabled', null);
                $button.find('i').removeClass('loading')
                $console.removeClass('loading')
            
                clearInterval(interval);
                $console.val(request.responseText).removeClass('loading');
            }
        });
        interval = setInterval(function () {
            $console.val(request.responseText);
        }, 1000);
        return false;
    });

    var venture_changed = function () {
        var $venture = $(this);
        var $role = $('select#id_venture_role');
        var selected = $role.val();
        $.post(
            '/ui/typeahead/roles/',
            {
                venture: $venture.val()
            },
            function (data, textStatus, jqXHR) {
                $role.html('');
                $.each(data['items'], function (i, item) {
                    if (selected === '' + item[0]) {
                        $role.append('<option selected="selected" value="' + item[0] + '">' + item[1] + '</option>');
                    } else {
                        $role.append('<option value="' + item[0] + '">' + item[1] + '</option>');
                    }
                });
            },
            'json'
        );

    };
    $('select#id_venture').change(venture_changed);
    $('select#id_venture').each(venture_changed);

    $('.datepicker').datepicker({format: 'yyyy-mm-dd', autoclose: true}).click(function(){
        $("input.datepicker[name!='" + $(this).attr('name') + "']").datepicker('hide');
    });

    var parseDate = function (input, format) {
        format = format || 'yyyy-mm-dd';
        var parts = input.match(/(\d+)/g), i = 0, fmt = {};
        format.replace(/(yyyy|dd|mm)/g, function(part) { fmt[part] = i++; });
        var date = new Date(0);
        date.setUTCFullYear(parts[fmt['yyyy']]);
        date.setUTCMonth(parts[fmt['mm']]-1);
        date.setUTCDate(parts[fmt['dd']]);
        return date;
    };
    var formatDate = function (d) {
        var pad = function (n) { return n < 10 ? '0' + n : n };
        return  d.getUTCFullYear() + '-' +
                pad(d.getUTCMonth()+1) + '-' +
                pad(d.getUTCDate());
    };
    var calendar = { years: [], months: [] };
    var now = new Date();
    var year = 2011;
    while (true) {
        if (new Date(year + 1, 0, 1, 12) >= now) {
            calendar.years.push({ label: year, value: year,
                                  css_class: 'btn-success' });
            break;
        }
        calendar.years.push({ label: year, value: year });
        year += 1;
    };
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
     'Nov', 'Dec'].forEach(function (label, i) {
         if (i === now.getUTCMonth()) {
            calendar.months.push({ label: label, value: i+1,
                                   css_class: 'btn-success' });
         } else {
            calendar.months.push({ label: label, value: i+1 });
         }
    });
    var calendar_tmpl = '<div class="btn-toolbar">' +
            '<div class="btn-group years" data-toggle="buttons-radio">' +
            '{{#years}}' +
            '<a href="#" class="btn {{css_class}}" data-value="{{value}}">' + 
            '{{label}}</a>' +
            '{{/years}}' +
            '</div>' +
            '<div class="btn-group months" data-toggle="buttons-radio">' +
            '{{#months}}' +
            '<a href="#" class="btn {{css_class}}" data-value="{{value}}">' +
            '{{label}}</a>' +
            '{{/months}}' +
            '</div>' +
            '</div>';

    $('.daterange-form .form-actions').each(function (i, form) {
        var $form = $(form);
        var $start = $form.find('input[name="start"]');
        var $end = $form.find('input[name="end"]');
        $form.prepend(Mustache.render(calendar_tmpl, calendar));
        $form.find('.years a').click(function (e) {
            var $this = $(this);
            var start_date = parseDate($start.val());
            start_date.setUTCFullYear($this.data('value'));
            $start.val(formatDate(start_date));
            if ($end) {
                var end_date = parseDate($end.val());
                end_date.setUTCFullYear($this.data('value'));
                $end.val(formatDate(end_date));
            };
        });
        $form.find('.months a').click(function (e) {
            var $this = $(this);

            var date = parseDate($start.val());
            date.setUTCMonth($this.data('value') - 1);
            date.setUTCDate(1);
            $start.val(formatDate(date));

            if ($end) {
                date.setUTCMonth($this.data('value'));
                date.setUTCDate(0);
                $end.val(formatDate(date));
            };
        });
    });
    $('form.search-form').submit(function () {
        var $form = $(this)
        var fields = $form.find('input[value!=""],textarea,select').serialize();
        var action = $form.attr('action') || '';
        window.location = action + '?' + fields;
        return false;
    });
    $('.close').click(function () {
        if ($(this).attr('data-dismiss') == 'alert'){
            $(this).parents('.alerts').filter(':first').remove();
        };
    })

    CMDBActiveTab = function (){
        var hash = location.hash
            , hashPieces = hash.split('?')
            , activeTab = $('[href=' + hashPieces[0] + ']');
        activeTab && activeTab.tab('show');
    }
    $('body').off('click.tab.data-api')
    $('body').on('click.scrolling-tabs', '[data-toggle="tab"], [data-toggle="pill"]', function (e) {
        if ($('.cmdb-ci-tabs')){
            $(this).tab('show');
        }
    });
    $(window).on('hashchange', function (){
        if ($('.cmdb-ci-tabs')){
            CMDBActiveTab();
        }
    });
    $(window).load(function (){
        if ($('.cmdb-ci-tabs')){
            CMDBActiveTab();
        }
    });
});
