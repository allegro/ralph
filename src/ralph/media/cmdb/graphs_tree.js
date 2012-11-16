(function () { 

var CMDB = {}; 

    CMDB.zoom_value = 1;
    CMDB.dragging = null;
    CMDB.requestAnimationFrame = function () {
        var fn = window.requestAnimationFrame || window.mozRequestAnimationFrame || window.webkitRequestAnimationFrame
            || window.msRequestAnimationFrame;
        fn.apply(window, arguments);
    };

    CMDB.graph_element = $("#chart")[0];

    function hypot(x, y) {
        return Math.sqrt(x*x + y*y);
    }

    function getInnerSVG(element) {
        var svg = element.clone();
        svg = $('<div />').append(svg);
        s = svg.html();
        return s;
    }

    function step(timestamp) {
        var el = CMDB.graph_element;
        var width = el.style.width;
        var height = el.style.height;
        var left = el.style.left;
        var top = el.style.top;
        values = calculate_new_xy(width, height, left, top, CMDB.zoom_value); 
        el.style.left = values['x'];
        el.style.top = values['y'];
        el.style.webkitTransform = 'scale(' + parseFloat(CMDB.zoom_value) + ')';
        CMDB.requestAnimationFrame(step);
    }

    CMDB.requestAnimationFrame(step);

    function calculate_new_xy(image_width, image_height, x_from_topleft, 
        y_from_topleft, zoom_factor) {
        var x_center = image_width / 2; 
        var y_center = image_height / 2
        var x_from_zoom_center = x_from_topleft - x_center;
        var y_from_zoom_center = y_from_topleft - y_center;
        angle  = Math.atan2(y_from_zoom_center, x_from_zoom_center);
        length = hypot(x_from_zoom_center, y_from_zoom_center);
        x_new = zoom_factor * length * Math.cos(angle);
        y_new = zoom_factor * length * Math.sin(angle);
        x_new_topleft = x_new + x_center;
        y_new_topleft = y_new + y_center;
        return {x: x_new_topleft, y: y_new_topleft};
    }

    $(document).bind('DOMMouseScroll mousewheel', function (e, delta) {
        delta = delta || e.detail || e.wheelDelta || e.originalEvent.wheelDeltaY;
        if (CMDB.zoom_value + (delta / 500) >= 1) {
            CMDB.zoom_value += delta / 500;
        }
        e.preventDefault();
        return false;
    });

    function saveSVG() {
    /* 
        SVG element has no method to get content of it. 
        To do it we must wrap it around html element to get inner content. 
        To be able to download svg to browser the only way is to open datauri, 
        and let user manually save svg.
     */
        var svg = $("svg:first");
        $(svg).attr('xmlns:xlink', 'http://www.w3.org/1999/xlink');
        $(svg).attr('xmlns', 'http://www.w3.org/2000/svg');
        var svgContents = getInnerSVG(svg);
        var dataURL = 'data:image/svg+xml,' + svgContents;
        var imgElement = document.createElement('img');
        var downloadData= "data:image/svg+xml," + svgContents;
        window.open(downloadData);
    }


    function main() {
        var radius = 860 / 2;
        var tree = d3.layout.tree()
            .size([360, radius - 120])
            .separation(function (a, b) { return (a.parent == b.parent ? 1 : 2) / a.depth; });
        var diagonal = d3.svg.diagonal.radial()
            .projection(function (d) { return [d.y, d.x / 180 * Math.PI]; });
        var vis = d3.select("svg")
            .attr("width", radius * 2)
            .attr("height", radius * 2 - 150)
            .append("g")
            .attr("transform", "translate(" + radius + "," + radius + ")");
        d3.json("/cmdb/graphs_ajax_tree?ci_id="+gup('ci'), function (json) {
            var nodes = tree.nodes(json);
            var link = vis.selectAll("path.link")
            .data(tree.links(nodes))
            .enter().append("path")
            .attr("class", "link")
            .attr("d", diagonal);

            var node = vis.selectAll("g.node")
            .data(nodes)
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", function (d) { return "rotate(" + (d.x - 90) + ")translate(" + d.y + ")"; });

            node.append("circle")
            .attr("r", 2.5);

            node.append("text")
            .attr("dy", ".31em")
            .attr("text-anchor", function (d) { return d.x < 180 ? "start" : "end"; })
            .attr("transform", function (d) { return d.x < 180 ? "translate(8)" : "rotate(180)translate(-8)"; })
            .text(function (d) { return d.name; });
    });
    }


function endMove() {
    $(this).removeClass('movable');
}

function startMove() {
    $('.movable').on('mousemove', function(event) {
        var thisX = event.pageX - $(this).width() / 2,
            thisY = event.pageY - $(this).height() / 2;

        $('.movable').offset({
            left: thisX,
            top: thisY
        });
    });
}

$(document).ready(function() {
    $("#save_svg_button").click(function() {
        saveSVG();
    });

    $("#chart").on('mousedown', function() {
        $(this).addClass('movable');
        startMove();
    }).on('mouseup', function() {
        $(this).removeClass('movable');
        endMove();
    });
    main();

});


})();
