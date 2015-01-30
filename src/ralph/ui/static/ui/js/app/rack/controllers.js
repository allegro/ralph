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
        $scope.$on('change_active_item', function (event, item) {
            $scope.activeItem = item;
            if (item.children.indexOf($scope.activeSlot) === -1) {
                $scope.activeSlot = null;
            }
        });
        $scope.$on('change_active_slot', function (event, slot) {
            $scope.activeSlot = slot;
        });
    }]);
