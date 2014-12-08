'use strict';

angular
    .module('data_center.controllers', [
            'ngCookies',
            'data_center.services',
            'data_center.directives'
        ]
    )
    .controller('DataCenterController', ['$scope', '$cookies', 'DataCenterModel', function ($scope, $cookies, DataCenterModel) {
        $scope.racks = DataCenterModel.query({dcId: $cookies.data_center_id});
    }]);
