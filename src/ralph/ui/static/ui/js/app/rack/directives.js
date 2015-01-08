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
