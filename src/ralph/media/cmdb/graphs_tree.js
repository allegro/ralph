(function () { 

var CMDB = {}; 
    CMDB.zoom_value = 1;
    CMDB.requestAnimationFrame = function () {
        var fn = window.requestAnimationFrame || window.mozRequestAnimationFrame || window.webkitRequestAnimationFrame
            || window.msRequestAnimationFrame;
        fn.apply(window, arguments);
    }
    CMDB.graph_element = $("#chart")[0];

    function hypot(x, y) {
        return Math.sqrt(x*x + y*y);
    }

    function step(timestamp) {
        var el = CMDB.graph_element;
        var width = el.style.width;
        var height = el.style.height;
        var left = el.style.left;
        var top = el.style.top;
        values = calculate_new_xy(width, height, left, top, CMDB.zoom_value); 
        el.style.position = 'absolute'; 
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

    function main() {
        var radius = 860 / 2;
        var tree = d3.layout.tree()
            .size([360, radius - 120])
            .separation(function (a, b) { return (a.parent == b.parent ? 1 : 2) / a.depth; });
        var diagonal = d3.svg.diagonal.radial()
            .projection(function (d) { return [d.y, d.x / 180 * Math.PI]; });
        var vis = d3.select("#chart").append("svg")
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

$(document).ready(main);

})();
