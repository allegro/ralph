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
        };
    })
    .directive('device', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/partials/rack/device.html',
            controller: function($scope) {
                $scope.setActiveItem = function(item) {
                    item.active = true;
                    $scope.$emit('change_active_item', item);
                };
                $scope.setActiveSlot = function(slot) {
                    $scope.$emit('change_active_slot', slot);
                };
            }
        };
    })
    .directive('listing', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/partials/rack/listing.html',
            link: function ($scope) {
                $scope.u_range = [];
                $scope.$on('change_active_item', function(event, item){
                    $scope.u_range = [];
                    if (typeof item !== 'undefined' && item !== null) {
                        var itemHeight = 1;     // for accessories...
                        if (typeof(item.height) !== 'undefined') {
                            itemHeight = item.height;
                        }
                        for (var i = item.position; i <= item.position+itemHeight-1; i++) {
                            $scope.u_range.push(i);
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
            require: '^rack',
            templateUrl: '/static/partials/rack/pdu_item.html',
            controller: function($scope) {
                $scope.setActiveItem = function(item) {
                    $scope.$emit('change_active_item', item);
                };
                $scope.setActiveSlot = function(slot) {
                    $scope.$emit('change_active_slot', slot);
                };
            }
        };
    });
