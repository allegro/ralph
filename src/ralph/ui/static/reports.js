/* The browser side of the functionality implemented in util/reports.py */

define(['jquery', 'moment', 'mustache'], function ($, moment, Mustache) {

    function AsyncLoader(settings) {
        this.url = settings.url;
        this.progressBar = settings.progressBar;
        this.etaEl = settings.etaEl;
        $(this.progressBar).show();
        this.setUndefinedBar()
    }

    AsyncLoader.prototype.start = function() {
        $.ajax({
            url: this.url,
            success: this.handleInitialReq,
            context: this,
        });
    };

    AsyncLoader.prototype.setUndefinedBar = function () {
        $(this.progressBar).addClass('progress-striped active');
        $(this.progressBar).children('.bar').css('width', '100%');
    };

    AsyncLoader.prototype.handleInitialReq = function (result, success, response) {
        var that;
        that = this;
        this.jobid = result.jobid;
        this.longIntervalHandle = setInterval(function () {
            $.ajax({
                url: that.url,
                data: {_report_jobid: that.jobid},
                success: that.handleUpdate,
                context: that,
            });
        }, 5e3);
        this.shortIntervalHandle = setInterval(function () {
            if(that.eta && that.eta.asSeconds() > 0) {
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
        var v = v.toString();
        return v.length === 1 ? '0' + v : v;
    }

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

    AsyncLoader.prototype.handleUpdate = function (result, success, response) {
        if (result.progress) {
            $(this.progressBar).removeClass('progress-striped active');
            $(this.progressBar).children('.bar').css(
                'width', result.progress.toString() + '%')
        }
        if (result.eta) {
            this.updateEtaWithSeconds(result.eta);
        }
        if (result.finished) {
            clearInterval(this.longIntervalHandle);
            clearInterval(this.shortIntervalHandle);
            $(this.progressBar).hide();
            $(this.etaEl).html('');
            window.location = this.url + '?' + $.param(
                    {_report_jobid: this.jobid, _report_finish: true});

        }
    };

    function setup(settings) {
        $(settings.progressBar).hide();
        $(settings.trigger).click(function (ev) {
            new AsyncLoader(settings).start();
            return false;
        });
    } 

    return {
        AsyncLoader: AsyncLoader,
        setup: setup
    }

});
