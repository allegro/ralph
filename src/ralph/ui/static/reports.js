/* The browser side of the functionality implemented in util/reports.py */

define(['jquery'], function ($) {

    function AsyncLoader(url) {
        this.url = url;
    }

    AsyncLoader.prototype.start = function() {
        $.ajax({
            url: this.url,
            success: this.handleInitialReq,
            context: this,
        });
    };

    AsyncLoader.prototype.handleInitialReq = function (result, success, response) {
        var that;
        that = this;
        this.jobid = result.jobid;
        $('#async-progress').show();
        this.intervalHandle = setInterval(function () {
            $.ajax({
                url: that.url,
                data: {_report_jobid: that.jobid},
                success: that.handleUpdate,
                context: that,
            });
        }, 4e3);
    };

    AsyncLoader.prototype.handleUpdate = function (result, success, response) {
        if (result.finished) {
            clearInterval(this.intervalHandle);
            window.location = this.url + '?' + $.param(
                    {_report_jobid: this.jobid, _report_finish: true});

        }
    };

    function setup(settings) {
        $(settings.progress_bar).hide();
        $(settings.trigger).click(function (ev) {
            new AsyncLoader(settings.url).start();
            return false;
        });
    } 

    return {
        AsyncLoader: AsyncLoader,
        setup: setup
    }

});
