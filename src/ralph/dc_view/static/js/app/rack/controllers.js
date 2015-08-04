(function(){
    'use strict';

    angular
        .module('rack.controllers', [
                'rack.services',
                'rack.directives',
            ]
        )
        .controller('RackController', ['$scope', 'rack', 'data_center', function ($scope, rack, data_center) {
            $scope.rack = rack;
            $scope.data_center = data_center;

            $scope.$on('change_active_item', function (event, item) {
                $scope.activeItem = item;
                if (
                    typeof(item.children) === 'undefined' ||
                    item.children.indexOf($scope.activeSlot) === -1
                ) {
                    $scope.activeSlot = null;
                }
            });
            $scope.$on('change_active_slot', function (event, slot) {
                $scope.activeSlot = slot;
            });
        }]);
})();
