(function(){
    'use strict';

    angular
        .module('data_center.controllers', [
                'data_center.services',
                'data_center.directives',
                'rack.services'
            ]
        )
        .controller('DataCenterController', ['$scope', '$stateParams', 'data_center', 'RackModel', function ($scope, $stateParams, data_center, RackModel) {
            var gridSize = 40;

            $scope.forms = {};
            $scope.data_center = data_center;

            $scope.setInfo = function(item) {
                $scope.info = item;
            };

            $scope.newRack = function(data_center, x, y) {
                var rack = new RackModel();
                rack.visualization_col = x;
                rack.visualization_row = y;
                rack.orientation = 'top';
                rack.server_room = '';
                rack.name = 'New rack';
                rack.new = true;
                data_center.rack_set.push(rack);
                $scope.$emit('edit_rack', rack);
            };

            $scope.updatePosition = function(event) {
                if (event.currentTarget != event.target)
                {
                    return;
                }
                var offsetX = event.offsetX || event.pageX - event.target.offsetLeft;
                var offsetY = event.offsetY || event.pageY - event.target.offsetTop;
                $scope.actualX = (offsetX - (offsetX % gridSize)) / gridSize;
                $scope.actualY = (offsetY - (offsetY % gridSize)) / gridSize;
            };

            $scope.addOrEdit = function(rack) {
                var rack_model = new RackModel(rack);
                var rack_promise = null;
                var success_msg = '';

                if (typeof(rack.id) !== 'undefined') {
                    rack_promise = rack_model.$update();
                    success_msg = 'updated';
                }
                else {
                    rack_promise = rack_model.$save();
                    success_msg = 'added to data center';
                }
                rack_promise.then(function(data) {
                    if (data.non_field_errors) {
                        $scope.forms.edit_form.$error.all = data.non_field_errors;
                    }
                    else {
                        rack.id = data.id;
                        rack.new = false;
                        rack.saved = true;
                        $scope.forms.edit_form.$error.all = null;
                        $scope.forms.edit_form.$success = ['The rack has been successfully ' + success_msg + '.'];
                        $scope.rack = undefined;
                    }
                });
            };

            $scope.$on('edit_rack', function (event, rack) {
                $scope.data_center.rack_set.forEach(function(rack) {
                    rack.active = false;
                });
                rack.active = true;
                rack.server_room = rack.server_room && rack.server_room.toString();
                $scope.rack = rack;
                $scope.forms.edit_form.action = 'edit';
                $scope.forms.edit_form.$error = {};
                $scope.forms.edit_form.$success = [];
            });
        }]);
})();
