(function(){
    'use strict';

    angular
        .module('data_center.services', [
                'ngResource'
            ]
        )
        .factory('DataCenterModel', ['$resource', function($resource){
            return $resource(
                '/api/data_center/:dcId/',
                {dcId: '@id'},
                {
                    addRack: {method: 'POST', params: {}}
                }
            );
        }]);
})();
