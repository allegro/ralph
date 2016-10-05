(function(angular, undefined) {
    'use strict';
    var app = angular.module('serverRoomVisualizationApp')
    app.constant('SETTINGS', {{ settings | safe }});
})(angular);
