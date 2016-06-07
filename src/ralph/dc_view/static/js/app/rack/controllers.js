(function(){
    'use strict';

    angular
        .module('rack.controllers', [
                'rack.services',
                'rack.directives',
                'common.directives',
            ]
        )
        .controller('RackController', ['$scope', 'rack', 'server_room', function ($scope, rack, server_room) {
            $scope.rack = rack;
            $scope.server_room = server_room;

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
