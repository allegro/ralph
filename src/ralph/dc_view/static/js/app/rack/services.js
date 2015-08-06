(function () {
    'use strict';

    angular
        .module('rack.services', [
                'ngResource'
            ]
        )
        .factory('RackModel', ['$resource', function($resource){
            return $resource('/api/rack/:rackId/',
                {
                    rackId: '@id'
                },
                {
                    update: {
                        method: 'PUT',
                    }
                }
            );
        }]);
}());
