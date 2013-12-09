/*jslint browser: true unparam: true*/
/*global define: false */
/* The browser side of the functionality implemented in util/reports.py */

define([
    'jquery', 'moment', 'mustache', 'deparam', 'bootbox'
], function ($, moment, Mustache, deparam, bootbox) {
    'use strict';

    function AsyncLoader(settings) {
        this.url = settings.url;
        this.progressBar = settings.progressBar;
        this.etaEl = settings.etaEl;
        $(this.progressBar).show();
        this.setUndefinedBar();
    }

    AsyncLoader.prototype.start = function (ev) {
        var url, bits;
        url = this.url || ev.target.href;
        bits = url.split('?', 2);
        this.url = bits[0];
        this.data = deparam(bits[1]);
        $.ajax({
            url: this.url,
            data: this.data,
            success: this.handleInitialReq,
            context: this
        });
    };

    AsyncLoader.prototype.setUndefinedBar = function () {
        $(this.progressBar).addClass('progress-striped active');
        $(this.progressBar).children('.bar').css('width', '100%');
    };

    AsyncLoader.prototype.handleInitialReq = function (result) {
        var that, data;
        that = this;
        this.jobid = result.jobid;
        data = $.extend({'_report_jobid': that.jobid}, this.data);
        this.longIntervalHandle = window.setInterval(function () {
            $.ajax({
                url: that.url,
                data: data,
                success: that.handleUpdate,
                context: that
            });
        }, 5e3);
        this.shortIntervalHandle = window.setInterval(function () {
            if (that.eta && that.eta.asSeconds() > 0) {
                that.eta.subtract(1, 'seconds');
                that.updateEtaDisplay();
            }
        }, 1e3);
    };

    AsyncLoader.prototype.updateEtaWithSeconds = function (eta) {
        this.eta = moment.duration(eta, 'seconds');
        this.updateEtaDisplay();
    };

    AsyncLoader.prototype.pad = function (v) {
        var s = v.toString();
        return s.length === 1 ? '0' + s : s;
    };

    AsyncLoader.prototype.updateEtaDisplay = function () {
        if (!this.eta) {
            return;
        }
        $(this.etaEl).html(Mustache.render('ETA: {{hours}}:{{minutes}}:{{seconds}}', {
            hours: this.pad(this.eta.hours()),
            minutes: this.pad(this.eta.minutes()),
            seconds: this.pad(this.eta.seconds())
        }));
    };

    AsyncLoader.prototype.handleUpdate = function (result) {
        var data;
        if (result.failed) {
            clearInterval(this.longIntervalHandle);
            clearInterval(this.shortIntervalHandle);
            $(this.etaEl).html('')
            $(this.progressBar).hide();
            bootbox.alert('Wygenerowanie wyniku nie powiodło się!');
            return;
        }
        if (result.progress) {
            $(this.progressBar).removeClass('progress-striped active');
            $(this.progressBar).children('.bar').css(
                'width',
                result.progress.toString() + '%'
            );
        }
        if (result.eta) {
            this.updateEtaWithSeconds(result.eta);
        }
        if (result.finished) {
            clearInterval(this.longIntervalHandle);
            clearInterval(this.shortIntervalHandle);
            $(this.progressBar).hide();
            $(this.etaEl).html('');
            data = $.param($.extend(
                {'_report_jobid': this.jobid, '_report_finish': true},
                this.data
            ));
            window.location = this.url + '?' + data;
        }
    };

    function setup(settings) {
        $(settings.progressBar).hide();
        $(settings.trigger).click(function (ev) {
            new AsyncLoader(settings).start(ev);
            return false;
        });
    }

    return {
        AsyncLoader: AsyncLoader,
        setup: setup
    };

});
