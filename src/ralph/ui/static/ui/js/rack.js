'use strict';

angular
    .module('racksApp', ['ngResource', 'ngCookies'])
    .factory('RackModel', ['$resource', function($resource){
        return $resource('/assets/api/rack/:rackId/devices/', {rackId: '@id'})
    }])
    .controller('RackController', ['$scope', '$cookies', 'RackModel', function ($scope, $cookies, RackModel) {
        $scope.rack = RackModel.get({rackId: $cookies.rack_id});
        $scope.$on('info', function (event, data) {
            $scope.info = data;
        })
    }])
    .controller('SideController', ['$scope', function ($scope) {
        $scope.setActiveItem = function (item) {
            $scope.activeItem = item;
            $scope.$emit('info', item);
        };
    }])
    .directive('device', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/partials/racks/device.html',
            link: function ($scope) {
                $scope.$watch('activeItem', function (newValue, oldValue){
                    if (newValue == $scope.item)
                        $scope.active = true;
                    else
                        $scope.active = false;
                })
            }
        };
    })
    .directive('listing', function () {
        return {
            restrict: 'A',
            templateUrl: '/static/partials/racks/listing.html',
            link: function ($scope) {
                $scope.$watch('activeItem', function (newValue, oldValue){
                    var i;
                    var item = $scope.activeItem;
                    $scope.u_range = [];
                    if (typeof item !== 'undefined' && item != null)
                        for (i = item.position; i <= item.position+item.height-1; i++)
                            $scope.u_range.push(i);
                })
            }
        };
    })
    .filter('range', function () {
        return function (input, total) {
            var i;
            total = parseInt(total);
            for (i = 0; i < total; i++)
            {
                input.push(i);
            }
            return input;
        };
    });
