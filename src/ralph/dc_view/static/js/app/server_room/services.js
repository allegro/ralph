(function(){
    'use strict';

    angular
        .module('server_room.services', [
                'ngResource'
            ]
        )
        .factory('ServerRoomModel', ['$resource', function($resource){
            return $resource(
                '/api/server_room/:srId/',
                {srId: '@id'},
                {
                    addRack: {method: 'POST', params: {}}
                }
            );
        }]);
})();
