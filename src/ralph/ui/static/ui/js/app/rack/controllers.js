'use strict';

angular
    .module('rack.controllers', [
            'ngCookies',
            'ngRoute',
            'rack.services',
            'rack.directives',
        ]
    )
    .controller('RackController', ['$scope', '$cookies', '$routeParams', 'RackModel', function ($scope, $cookies, $routeParams, RackModel) {
        var rackId;
        if($routeParams.rackId) {
            rackId = $routeParams.rackId;
        }
        else {
            rackId = $cookies.rack_id;
        }

        $scope.rack = RackModel.get({rackId: rackId});
        $scope.$on('info', function (event, data) {
            $scope.info = data;
        });
    }])
    .controller('SideController', ['$scope', function ($scope) {
        $scope.setActiveItem = function (item) {
            $scope.activeItem = item;
            $scope.$emit('info', item);
        };
    }]);
