{% load cache staticfiles %}

{% cache 3600 settings_js %}
    (function(angular, undefined) {
        'use strict';
        var app = angular.module('serverRoomVisualizationApp')
        app.constant('SETTINGS', {{ settings | safe }});
    })(angular);
{% endcache %}
