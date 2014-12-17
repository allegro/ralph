'use strict';

angular
    .module('rack.directives', [])
    .directive('rack', function () {
        return {
            restrict: 'E',
            scope: {
                devices: '=',
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
                    $scope.$emit('info', item);
                };
            }
        };
    })
    .directive('listing', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/partials/rack/listing.html',
        };
    });
