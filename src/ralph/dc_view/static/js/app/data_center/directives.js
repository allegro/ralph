(function(){
    'use strict';

    angular
        .module('data_center.directives', ['rack.services'])
        .directive('rackTop', ['$document', 'RackModel', function ($document, RackModel) {
            return {
                restrict: 'E',
                templateUrl: '/static/partials/data_center/rack.html',
                scope: {
                    rack: '=',
                    mode: '=',
                    dc: '='
                },
                link: function(scope, element) {
                    var gridSize = 40;
                    var startX = 0, startY = 0;
                    var offset;
                    var changedPosition = false;
                    scope.rack.active = false;
                    element.on('mousedown', function(event) {
                        event.preventDefault();
                        offset = element.offset();
                        // offset = {left: 0, top: 0};
                        startX = event.pageX - offset.left;
                        startY = event.pageY - offset.top;
                        if (scope.mode == 'edit') {
                            $document.on('mousemove', mousemove);
                            $document.on('mouseup', mouseup);
                            scope.is_move = true;
                        }
                    });
                    function mousemove(event) {
                        var can_drop = true;
                        var x = event.pageX - offset.left;
                        var y = event.pageY - offset.top;
                        var position_x = (x - (x % gridSize)) / gridSize;
                        var position_y = (y - (y % gridSize)) / gridSize;
                        angular.forEach(scope.dc.rack_set, function(value) {
                            var isSelectedRack = value.id !== scope.rack.id;
                            var isOccupiedSpace = value.visualization_col == position_x && value.visualization_row == position_y;
                            if (isSelectedRack && isOccupiedSpace) {
                                can_drop = false;
                            }
                        });
                        if(can_drop) {
                            scope.rack.visualization_col = position_x;
                            scope.rack.visualization_row = position_y;
                            changedPosition = true;
                        }
                        scope.can_drop = can_drop;
                    }
                    function mouseup() {
                        $document.unbind('mousemove', mousemove);
                        $document.unbind('mouseup', mouseup);
                        if (changedPosition) {
                            new RackModel(scope.rack).$update();
                        }
                        scope.is_move = false;
                    }

                    scope.rotate = function(direction) {
                        var orientations = ['top', 'right', 'bottom', 'left'];
                        var index = orientations.indexOf(scope.rack.orientation) + direction;
                        if (index < 0) {
                            index = orientations.length -1;
                        }
                        if (index > orientations.length -1) {
                            index = 0;
                        }
                        scope.rack.orientation = orientations[index];
                        new RackModel(scope.rack).$update();
                    };

                    scope.edit = function(rack) {
                        scope.$emit('edit_rack', rack);
                    };
                }
            };
        }]);
})();
