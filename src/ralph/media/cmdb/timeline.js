/*
 * JavaScript Pretty Date
 * Copyright (c) 2011 John Resig (ejohn.org)
 * Licensed under the MIT and GPL licenses.
 */

// Takes an ISO time and returns a string representing how
// long ago the date represents.
function prettyDate(time){
    var date = new Date((time || "").replace(/-/g,"/").replace(/[TZ]/g," ")),
        diff = (((new Date()).getTime() - date.getTime()) / 1000),
        day_diff = Math.floor(diff / 86400);
            
    if ( isNaN(day_diff) || day_diff < 0 || day_diff >= 31 )
        return;
            
    return day_diff == 0 && (
            diff < 60 && "just now" ||
            diff < 120 && "1 minute ago" ||
            diff < 3600 && Math.floor( diff / 60 ) + " minutes ago" ||
            diff < 7200 && "1 hour ago" ||
            diff < 86400 && Math.floor( diff / 3600 ) + " hours ago") ||
        day_diff == 1 && "Yesterday" ||
        day_diff < 7 && day_diff + " days ago" ||
        day_diff < 31 && Math.ceil( day_diff / 7 ) + " weeks ago";
}

// If jQuery is included in the page, adds a jQuery plugin to handle it as well
if ( typeof jQuery != "undefined" )
    jQuery.fn.prettyDate = function(){
        return this.each(function(){
            var date = prettyDate(this.title);
            if ( date )
                jQuery(this).text( date );
        });
    };


function load_data(url){
    $('#placeholder').html(loading());
    $('#changes_table').html('');
    $('#plot_title').html('');
    $('#changes_table').removeClass('table table-striped table-bordered table-condensed');
    $.get(url, function(data){
        setup(data);
        $('#changes_table').addClass('table table-striped table-bordered table-condensed');
        }).error(function(e){
            $('#placeholder').html('<p class="text-error"><b>Error loading data.</b></p>');
            console.log(e.responseText);
    });
}

function handle_manual_click(){
    var display = this.event.currentTarget.previousSibling.style.display = 'block';
    display.style.display = 'block';
    display.style.fontSize = '30px';
}

function annotate_manual(plot, data, plot_title, issuetracker_url, min, max){

    var aggregatedData = [];
    var text_content = '';
    var day_and_hour;
    var d;
    var href_link;
    var point_text_template = '<div style="display:none">{{comment}}</div><div class="pointer" onclick="handle_manual_click()"> * </div>';
    var row_template = '<tr class="{{row_class}}"><td>{{date}}</td><td>{{comment}}</td><td>{{author}}</td><td>{{{href_link}}}</td><td><a href="{{issuetracker_url}}/{{external_key}}">{{external_key}}</a><td>{{changed_cis}}</td><td>{{failed_cis}}</tr>';
    $('#plot_title').html(plot_title);
    $("#changes_table").html('<tr><th>Time</th><th>Comment</th><th>Author</th><th>View</th><th>External key</th><th>Changed CIs</th><th>Failed CI</th></tr>');

    for (var i=0; i<data.length; i++){
        obj = data[i];
        d = new Date(data[i].time);
        t = d.getTime();
        if (t<min || t>max){
            continue 
        }
        day_and_hour = t;
        o = plot.pointOffset({ x: d, y: plot.getAxes().yaxis.datamax});
        point_content = Mustache.render(point_text_template, {
            'comment': data[i].comment
        });

        href_link = Mustache.render(
                '<a href="/cmdb/changes/change/{{id}}">View</a>',{
                    'id': obj['id']
        });
        external_key = obj.external_key;
        if(data[i].errors_count>0)
        {
            row_class='row_error'
        }
        else
        {
            row_class=''
        }
        $("#changes_table").append(Mustache.render(row_template, {
            'date': prettyDate(data[i].time),
            'comment': data[i].comment,
            'author': data[i].author,
            'href_link':  href_link,
            'external_key': external_key,
            'issuetracker_url': issuetracker_url,
            'failed_cis': data[i].errors_count,
            'changed_cis': data[i].success_count,
            'row_class': row_class
        }));

        $("#placeholder").append(Mustache.render('<div style="position:absolute;left:{{left_position}}px;top:{{top_position}}px">{{{point_content}}}</div>',{
            'left_position': o.left + 4,
            'top_position':  o.top,
            'point_content': point_content
        }));
    }
}

function aggregate(data){
    var aggregatedData = [];
    for (var i=0; i<data.length;i++)
    {
        var d = new Date(data[i].time);
        d.setMinutes(0);
        d.setSeconds(0);
        d = d.getTime(); // flot required conversion.
        var day_and_hour = d;
        aggregatedData[day_and_hour] = 
            aggregatedData[day_and_hour] ? 
            aggregatedData[day_and_hour]+1 : 1;
    }
    var keys = [];
    for (var key in aggregatedData) {
        if (aggregatedData.hasOwnProperty(key)) {
            keys.push([key, aggregatedData[key]]);
        }
    }
    return keys;
}

function setup(data){
    var d = new Date();
    var n = d.getHours();

    var options = {
        xaxis: { mode: "time", timeformat: "%d/%m %h:%M"},
        series: {
            lines: { show: true },
            points: { show: true }
        },
        selection: {
            mode:  "x",
            color: 'yellow'
        }
    };
    var data_warnings = aggregate(data.agent_warnings);
    var data_errors = aggregate(data.agent_errors);

    var plotdata = [
        {'label' : 'Puppet warnings', 'data' : data_warnings, 'clickable' : true},
        {'label' : 'Puppet errors', 'data' : data_errors},
    ];

    var placeholder = $("#placeholder");
    placeholder.bind("plotselected", function (event, ranges){
        plot = $.plot(placeholder, plotdata,
            $.extend(true, {}, options, {
                xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to }
            }));
        annotate_manual(plot, data.manual, data.plot_title, data.issuetracker_url, ranges.xaxis.from, ranges.xaxis.to);
    });

    placeholder.bind("plotunselected", function (event) {
        //$("#selection").text("Click drawing to unselect");
        options['xaxis'] =  { mode: "time", timeformat: "%d/%m %h:%M" },
        plot = $.plot(placeholder, plotdata , options);
        plot.setSelection({ xaxis: { from: 0, to: 0 } });
        plot.setupGrid();
        plot.draw();
        annotate_manual(plot, data.manual, data.plot_title, data.issuetracker_url);
    });

    plot = $.plot(placeholder, plotdata , options);
    annotate_manual(plot, data.manual, data.plot_title, data.issuetracker_url);

};


function loading(){
    return '<b>Loading please wait...</b>';
};
