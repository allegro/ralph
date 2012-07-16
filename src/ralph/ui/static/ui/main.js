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
        }, 'json');
    });
    $('div.add-popover[').popover({
        placement: 'left'
    });
    $('a[rel="tooltip"]').tooltip();
    $('.select-all').click(function () {
        $('input[name="select"]').prop('checked', true);
    });
    $('.select-pages').click(function () {
        $('input[name="select"]').prop('checked', true);
        $('input[name="selectall"]').prop('checked', true);
    });
    $('.select-none').click(function () {
        $('input[name="select"]').prop('checked', false);
        $('input[name="selectall"]').prop('checked', false);
    });
    $('.select-toggle').click(function() {
        $('input[name="select"]').each(function () {
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
});
