(function(){
    'use strict';

    angular
        .module('dataCenterVisualizationApp', [
                'ui.router',
                'common.filters',
                'ncy-angular-breadcrumb',
                'data_center.controllers',
                'rack.controllers',
                'angular-loading-bar',
            ]
        )
        .config(['$httpProvider', '$stateProvider', '$urlRouterProvider', '$breadcrumbProvider', function($httpProvider, $stateProvider, $urlRouterProvider, $breadcrumbProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
            $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

            $urlRouterProvider.otherwise('/dc');
            $breadcrumbProvider.setOptions({
                template: 'bootstrap2'
            });
            $stateProvider
                .state('data_center', {
                    url: '/dc',
                    templateUrl: '/static/partials/data_center/dc.html',
                    ncyBreadcrumb: {
                        label: 'Data Centers'
                    }
                })
                .state('data_center.detail', {
                    url: '/{dcId:[0-9]{1,4}}',
                    views: {
                        '@': {
                            templateUrl: '/static/partials/data_center/data_center.html',
                            controller: 'DataCenterController',
                        },
                        'rack-list@': {
                            templateUrl: '/static/partials/data_center/rack_list.html',
                            controller: ['$scope', 'data_center', function($scope, data_center){
                                $scope.data_center = data_center;
                            }],
                        }
                    },
                    resolve: {
                        data_center: ['$stateParams', 'DataCenterModel', function($stateParams, DataCenterModel) {
                            return DataCenterModel.get({dcId: $stateParams.dcId});
                        }]
                    },
                    ncyBreadcrumb: {
                        label: '{{ data_center.name || rack.info.data_center.name }}',
                    }
                })
                .state('data_center.detail.rack', {
                    url: '/rack/{rackId:[0-9]{1,4}}',
                    views: {
                        '@': {
                            templateUrl: '/static/partials/data_center/data_center.detail.rack.html',
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
