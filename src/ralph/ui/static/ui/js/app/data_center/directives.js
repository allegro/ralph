'use strict';

angular
    .module('data_center.directives', [])
    .directive('rackTop', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/partials/data_center/rack.html',
            scope: {
                rack: '=',
            }
        };
    });
