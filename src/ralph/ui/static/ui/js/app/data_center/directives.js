'use strict';

angular
    .module('data_center.directives', [])
    .directive('rack', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/partials/data_center/rack.html',
            scope: {
                id: '@',
                x: '@',
                y: '@',
                name: '@',
                datacenter: '='
            }
        };
    });
