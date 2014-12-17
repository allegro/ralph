'use strict';

angular
    .module('dataCenterVisualizationApp', [
            'ngRoute',
            'common.filters',
            'data_center.controllers',
            'rack.controllers',
        ]
    )
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: '/static/partials/data_center/data_center_view.html',
                controller: 'DataCenterController'
            })
            .when('/rack/:rackId', {
                templateUrl: '/static/partials/rack/rack_view.html',
                controller: 'RackController'
            })
            .otherwise('/');
    }]);

angular
    .module('rackVisualizationApp', [
            'ngRoute',
            'common.filters',
            'rack.controllers',
        ]
    )
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider
            .when('/', {
                templateUrl: '/static/partials/rack/rack_view.html',
                controller: 'RackController'
            })
            .otherwise('/');
    }]);
