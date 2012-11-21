(function () {

    /* Performance hack for icons.
       Render big sprites image into the canvas. Then, extract small portions of 
       canvas into another canvas to be able to export image data. 
       Now, image data embed into svg 'image' node using base64 encoding.

       Yes, it IS event >10 x faster than using viewport on big native svg image data.
     */

    function fromCanvasToSvg(sourceCanvas, targetSVG, x, y, width, height) {
        var imageData = sourceCanvas.getContext('2d').getImageData(
            x, y, width, height);
        var newCanvas = document.createElement("canvas");
        var imgDataurl;
        newCanvas.width = width; newCanvas.height = height;
        newCanvas.getContext("2d").putImageData(imageData, 0, 0);
        imgDataurl = newCanvas.toDataURL("image/png");
        targetSVG.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", imgDataurl);
    }

    function getInnerSVG(element) {
        var svg = element.clone();
        svg = $('<div />').append(svg);
        s = svg.html();
        return s;
    }

    function typeToColor(type) {
        if (type == 1) {
            return '#ddd';
        } else if (type == 2) {
            return 'red';
        } else {
            return 'black';
        };
    }

    function handleMouseClick(node) {
        $('text').each(function (index, value) {
                $(value).attr('class', '');
        });
        $('path').each(function (index, value) {
                $(value).attr('class', '');
        });

        $(node.ui).children().first().attr('class', 'focused');
        
        $("#cmdb_name").html(node.data.name);
        $("#cmdb_link").html("<a target='_blank' href='/cmdb/ci/view/" + node.data.id + "'>View</a>");
        $("#check_impact_link").html("<a target='_blank' href='/cmdb/graphs?ci=" + node.data.id + "'>View impact</a>");
        $(node.links).each(function (index, el) {
            $(el.ui).attr('class','focused');
        }
        );
    }

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

    function drawGraph(data, spriteCanvas) {
        var graph = Viva.Graph.graph();
        var graphics = Viva.Graph.View.svgGraphics(), nodeSize = 32;
        var renderer = Viva.Graph.View.renderer(graph, {
             container: document.getElementById('graphDiv'),
            graphics: graphics
            });
        renderer.run();
        graphics.node(function (node) {
            var spriteName = node.data.icon.replace('fugue-', '');
            var coord = fugueData[spriteName];
            var image = Viva.Graph.svg('image');
            fromCanvasToSvg(spriteCanvas, image, coord[0], coord[1], 16, 16);
            image.attr('width', 16).attr('height', 16);
            var g = Viva.Graph.svg('g').attr('width', 224).attr('height', 180);
            var e = Viva.Graph.svg('text').attr('width', 124)
            .attr('height', 80).attr('font-size', '7');
            e.textContent = node.data.name;
            g.appendChild(e);
            g.appendChild(image);
            $(g).click(function (e) {
                handleMouseClick(node);
                e.stopPropagation();
            });

            return g;
        }).placeNode(function (nodeUI, pos){
                var nu = nodeUI;
                $(nu).children()[0].attr('x', pos.x+10).attr('y', pos.y+10);
                $(nu).children()[1].attr('x', pos.x-10).attr('y', pos.y-10);
        });
        /* Arrows setup */
        var createMarker = function (id) {
            return Viva.Graph.svg('marker')
                       .attr('id', id)
                       .attr('viewBox', "0 0 10 10")
                       .attr('refX', "10")
                       .attr('refY', "5")
                       .attr('markerUnits', "strokeWidth")
                       .attr('markerWidth', "10")
                       .attr('markerHeight', "2")
                       .attr('orient', "auto");
        },
        
        marker = createMarker('Triangle');
        marker.append('path').attr('d', 'M 0 0 L 10 5 L 0 10 z');
        // Marker should be defined only once in <defs> child element of root <svg> element:
        var defs = graphics.getSvgRoot().append('defs');
        defs.append(marker);
        var geom = Viva.Graph.geom(); 
        graphics.link(function (link) {
            // Notice the Triangle marker-end attribe:
            return Viva.Graph.svg('path')
                       .attr('stroke', link.data.color)
                       .attr('marker-end', 'url(#Triangle)');
        }).placeLink(function (linkUI, fromPos, toPos) {
            // Here we should take care about 
            //  "Links should start/stop at node's bounding box, not at the node center."
            // For rectangular nodes Viva.Graph.geom() provides efficient way to find
            // an intersection point between segment and rectangle
            var toNodeSize = nodeSize,
                fromNodeSize = nodeSize;
            var from = geom.intersectRect(
                    // rectangle:
                            fromPos.x - fromNodeSize / 2, // left
                            fromPos.y - fromNodeSize / 2, // top
                            fromPos.x + fromNodeSize / 2, // right
                            fromPos.y + fromNodeSize / 2, // bottom
                    // segment:
                            fromPos.x, fromPos.y, toPos.x, toPos.y) 
                       || fromPos; // if no intersection found - return center of the node
            var to = geom.intersectRect(
                    // rectangle:
                            toPos.x - toNodeSize / 2, // left
                            toPos.y - toNodeSize / 2, // top
                            toPos.x + toNodeSize / 2, // right
                            toPos.y + toNodeSize / 2, // bottom
                    // segment:
                            toPos.x, toPos.y, fromPos.x, fromPos.y) 
                        || toPos; // if no intersection found - return center of the node
            var data = 'M' + from.x + ',' + from.y +
                       'L' + to.x + ',' + to.y;
            linkUI.attr("d", data);
        });
        for (var i=0; i<data.nodes.length; i++) {
                graph.addNode(data.nodes[i][0], {'id': data.nodes[i][0], 'name':data.nodes[i][1],'icon': data.nodes[i][2]});
        };
        for (var i=0; i<data.relations.length; i++) {
            graph.addLink(
                data.relations[i].parent, 
                data.relations[i].child, {'color': typeToColor(data.relations[i].type), 
                'type': data.relations[i].type});
        };
    }


    var fugueData = "";
    $(document).ready(function () {
        var MAX_RELATIONS_COUNT = 100;
        var can, ctx, img, spriteURL;

        /* 
          Don't make additional ajax call, just use graph_data directly. 
         */
        var graph_data = CMDB.graph_data;
        if (typeof graph_data.nodes == 'undefined') {
            // Displaying form, no data yet
            return;
        };
        if (graph_data.nodes.length > MAX_RELATIONS_COUNT) {
            alert('To many relations to draw a graph.');
        } else {
            $("#save_svg_button").click(saveSVG);
            fugueData = "";
            jQuery.ajax({
                url: '/static/cmdb/fugue-icons.json',
                success: function (html) {
                        fugueData = html;
            },
            async:false
            });
            can = document.createElement('canvas')
            can.style.display = 'none';
            ctx = can.getContext('2d');
            img = new Image();
            $(img).load(function () {
                can.width = img.width;
                can.height = img.height;
                ctx.drawImage(img, 0, 0, img.width, img.height);
                drawGraph(graph_data, can);
            });
            spriteURL = '/static/fugue-icons.png';
            img.src = spriteURL; 
        };
    });
})();

