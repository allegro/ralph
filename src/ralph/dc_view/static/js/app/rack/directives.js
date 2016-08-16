(function(){
    'use strict';

    angular
        .module('rack.directives', [])
        .directive('rack', function () {
            return {
                restrict: 'E',
                scope: {
                    devices: '=',
                    pdus: '=',
                    side: '@',
                    info: '='
                },
                templateUrl: '/static/partials/rack/rack.html',
                link: function(scope, element) {
                    element.on('mousemove', function(event) {
                        if (event.target.className === 'devices') {
                            var free_position = scope.info.max_u_height - Math.floor(event.offsetY / 25);
                            scope.$broadcast('hover-on-empty-space', {'position': free_position});
                        }
                    });
                    element.on('mouseout', function() {
                        if (event.target.className !== 'devices') {
                            scope.$broadcast('hover-on-empty-space', {'position': 0});
                        }
                    });
                }
            };
        })
        .directive('addItem', function () {
            return {
                restrict: 'E',
                template: [
                    '<div ng-class="{hide: position == 0}" class="device add-btn height-u-1 position-u-{{ position }}" title="Click with CTRL key pressed to open in new tab">',
                        '<i class="fa fa-plus"></i>',
                    '</div>'
                ].join('\n'),
                link: function(scope, element, attr) {
                    scope.position = 0;
                    scope.$on('hover-on-empty-space', function(event, data) {
                        scope.$apply(function () {
                            scope.position = data.position;
                        })
                    });
                }
            }
        })
        .directive('deviceItem', function () {
            return {
                restrict: 'E',
                scope: {
                    device: '=',
                    side: '='
                },
                templateUrl: '/static/partials/rack/device_item.html',
                link: function(scope) {
                    scope.setActiveItem = function(item) {
                        item.active = true;
                        scope.$emit('change_active_item', item);
                    };
                    scope.setActiveSlot = function(slot) {
                        scope.$emit('change_active_slot', slot);
                    };
                    scope.getLayout = function() {
                        return scope.device[scope.side + '_layout'];
                    };
                }
            };
        })
        .directive('listing', function () {
            return {
                restrict: 'E',
                templateUrl: '/static/partials/rack/listing.html',
                link: function (scope) {
                    scope.u_range = [];
                    scope.$on('change_active_item', function(event, item){
                        scope.u_range = [];
                        if (typeof item !== 'undefined' && item !== null) {
                            var itemHeight = 1;     // for accessories...
                            if (typeof(item.height) !== 'undefined') {
                                itemHeight = item.height;
                            }
                            for (var i = item.position; i <= item.position+itemHeight-1; i++) {
                                scope.u_range.push(i);
                            }
                        }
                    });
                }
            };
        })
        .directive('pduItem', function () {
            return {
                restrict: 'E',
                scope: {
                    pdu: '='
                },
                templateUrl: '/static/partials/rack/pdu_item.html',
                link: function(scope) {
                    scope.setActiveItem = function(item) {
                        scope.$emit('change_active_item', item);
                    };
                    scope.setActiveSlot = function(slot) {
                        scope.$emit('change_active_slot', slot);
                    };
                }
            };
        });
})();
