
function load_data(){
    $.get("/cmdb/changes/timeline_ajax", function(data){
            setup(data);
        }).error(function(e){
            alert('Error loading data.');
            console.log(e.responseText);
    });
}

function handle_manual_click(){
    var display = this.event.currentTarget.previousSibling.style.display = 'block';
    display.style.display = 'block';
    display.style.fontSize = '30px';
}

function annotate_manual(plot, data, min, max){

    var aggregatedData = [];
    var text_content = '';
    var day_and_hour;
    var d;
    var href_link;
    var point_text_template = '<div style="display:none">{{comment}}</div><div class="pointer" onclick="handle_manual_click()"> * </div>';
    var row_template = '<tr><td>{{date}}</td><td>{{comment}}</td><td>{{author}}</td><td>{{{href_link}}}</td></tr>';

    $("#changes_table").html('<tr><th>Time</th><th>Comment</th><th>Author</th><th>View</th></tr>');

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

        $("#changes_table").append(Mustache.render(row_template, {
            'date': d,
            'comment': data[i].comment,
            'author': data[i].author,
            'href_link':  href_link,
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
    var options = {
        xaxis: { mode: "time", timeformat: "%d/%m %h:%M" },
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
        annotate_manual(plot, data.manual, ranges.xaxis.from, ranges.xaxis.to);
    });

    placeholder.bind("plotunselected", function (event) {
        //$("#selection").text("Click drawing to unselect");
        options['xaxis'] =  { mode: "time", timeformat: "%d/%m %h:%M" },
        plot = $.plot(placeholder, plotdata , options);
    plot.setSelection({ xaxis: { from: 0, to: 0 } });
    plot.setupGrid();
    plot.draw();
    annotate_manual(plot, data.manual);
    });

    plot = $.plot(placeholder, plotdata , options);
    annotate_manual(plot, data.manual);
};
