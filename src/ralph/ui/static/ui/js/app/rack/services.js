'use strict';

angular
    .module('rack.services', [
            'ngResource'
        ]
    )
    .factory('RackModel', ['$resource', function($resource){
        return $resource('/assets/api/rack/:rackId/',
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
