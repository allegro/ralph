'use strict';

angular
    .module('data_center.controllers', [
            'ngCookies',
            'data_center.services',
            'data_center.directives',
            'rack.services'
        ]
    )
    .controller('DataCenterController', ['$scope', '$cookies', 'DataCenterModel', 'RackModel', function ($scope, $cookies, DataCenterModel, RackModel) {
        var gridSize = 40;
        $scope.data_center = DataCenterModel.get({dcId: $cookies.data_center_id});

        $scope.setInfo = function(item) {
            $scope.info = item;
        };

        $scope.updatePosition = function(event) {
            var offsetX = event.offsetX || event.pageX - event.target.offsetLeft;
            var offsetY = event.offsetY || event.pageY - event.target.offsetTop;
            $scope.actualX = (offsetX - (offsetX % gridSize)) / gridSize;
            $scope.actualY = (offsetY - (offsetY % gridSize)) / gridSize;
        };

        $scope.updateRack = function(rack) {
            new RackModel(rack).$update();
        };

        $scope.$on('edit_rack', function (event, rack) {
            angular.forEach($scope.data_center.rack_set, function(rack) {
                rack.active = false;
            });
            rack.active = true;
            $scope.rack = rack;
        });
    }]);
