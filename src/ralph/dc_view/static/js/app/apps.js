(function(){
    'use strict';

    angular
        .module('serverRoomVisualizationApp', [
                'ui.router',
                'common.filters',
                'ncy-angular-breadcrumb',
                'server_room.controllers',
                'rack.controllers',
                'angular-loading-bar',
            ]
        )
        .config(['$httpProvider', '$stateProvider', '$urlRouterProvider', '$breadcrumbProvider', function($httpProvider, $stateProvider, $urlRouterProvider, $breadcrumbProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
            $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

            $urlRouterProvider.otherwise('/sr');
            $breadcrumbProvider.setOptions({
                template: '<ul class="breadcrumbs">' +
                '<li ng-repeat="step in steps" ng-class="{current: $last}" ng-switch="$last || !!step.abstract">' +
                '<a ng-switch-when="false" href="{{step.ncyBreadcrumbLink}}">{{step.ncyBreadcrumbLabel}}</a>' +
                '<span ng-switch-when="true">{{step.ncyBreadcrumbLabel}}</span>' +
                '</li>'+
                '</ul>'
            });
            $stateProvider
                .state('server_room', {
                    url: '/sr',
                    templateUrl: '/static/partials/server_room/sr.html',
                    ncyBreadcrumb: {
                        label: 'DC Visualization'
                    }
                })
                .state('server_room.detail', {
                    url: '/{srId:[0-9]{1,4}}',
                    views: {
                        '@': {
                            templateUrl: '/static/partials/server_room/server_room.html',
                            controller: 'ServerRoomController',
                        },
                        'rack-list@': {
                            templateUrl: '/static/partials/server_room/rack_list.html',
                            controller: ['$scope', '$filter', '$state', 'server_room', function($scope, $filter, $state, server_room){
                                $scope.server_room = server_room;
                                $scope.submit_search = function() {
                                    var filtered_racks = $filter('filter')($scope.server_room.rack_set, $scope.rack_filter);
                                    if(filtered_racks !== undefined && filtered_racks.length == 1) {
                                        $state.go(
                                            'server_room.detail.rack',
                                            {
                                                srId: $scope.server_room.id,
                                                rackId: filtered_racks[0].id
                                            }
                                        );
                                    }
                                };
                            }],
                        }
                    },
                    resolve: {
                        server_room: ['$stateParams', 'ServerRoomModel', function($stateParams, ServerRoomModel) {
                            return ServerRoomModel.get({srId: $stateParams.srId});
                        }]
                    },
                    ncyBreadcrumb: {
                        label: '{{ server_room.name || rack.info.server_room.name }}',
                    }
                })
                .state('server_room.detail.rack', {
                    url: '/rack/{rackId:[0-9]{1,4}}',
                    views: {
                        '@': {
                            templateUrl: '/static/partials/server_room/server_room.detail.rack.html',
                            controller: 'RackController'
                        },
                    },
                    resolve: {
                        rack: ['$stateParams', 'RackModel', function($stateParams, RackModel) {
                            return RackModel.get({rackId: $stateParams.rackId});
                        }],
                    },
                    ncyBreadcrumb: {
                        label: '{{ rack.info.name }}',
                    }
                });
        }]);
})();
