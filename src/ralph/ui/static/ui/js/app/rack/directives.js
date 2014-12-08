'use strict';

angular
    .module('rack.directives', [])
    .directive('device', function () {
        return {
            restrict: 'E',
            templateUrl: '/static/partials/rack/device.html',
            link: function ($scope) {
                $scope.$watch('activeItem', function (newValue){
                    if (newValue == $scope.item) {
                        $scope.active = true;
                    }
                    else {
                        $scope.active = false;
                    }
                });
            }
        };
    })
    .directive('listing', function () {
        return {
            restrict: 'A',
            templateUrl: '/static/partials/rack/listing.html',
            link: function ($scope) {
                $scope.$watch('activeItem', function (){
                    var item = $scope.activeItem;
                    $scope.u_range = [];
                    if (typeof item !== 'undefined' && item !== null)
                        for (var i = item.position; i <= item.position+item.height-1; i++) {
                            $scope.u_range.push(i);
                        }
                });
            }
        };
    });
