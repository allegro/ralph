'use strict';

angular
    .module('data_center.controllers', [
            'ngCookies',
            'data_center.services',
            'data_center.directives'
        ]
    )
    .controller('DataCenterController', ['$scope', '$cookies', 'DataCenterModel', function ($scope, $cookies, DataCenterModel) {
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
    }]);
