var serviceLocator = angular.injector(['ng', 'dataCenterVisualizationApp']);
var $controllers = serviceLocator.get('$controller');
var scope = {};
var dataCenterMock = {
    rack_set: []
};
var rackModel;

QUnit.module('Data Center controllers', {
    setup: function () {
        scope = serviceLocator.get('$rootScope').$new();
        rackModel = serviceLocator.get('RackModel');
        $controllers('DataCenterController', {$scope: scope, data_center: dataCenterMock, RackModel: rackModel});
    }
});

test('newRack should add rack to rack_set', function(){
    ok(scope.data_center.rack_set.length === 0);
    scope.newRack(1, 1);
    ok(scope.data_center.rack_set.length === 1);
});

test('updatePosition should not update variables actualX and actualY when target is not equal currentTarget', function() {
    var mockedPos = 1;
    scope.actualX = mockedPos;
    scope.actualY = mockedPos;
    var mockedEvent = {
        target: {element: 'rack'},
        currentTarget: {element: 'grid'},
        offsetX: 800,
        offsetY: 400,
    };
    scope.updatePosition(mockedEvent);
    ok(scope.actualX == mockedPos);
    ok(scope.actualY == mockedPos);
});

test('updatePosition should update variables actualX and actualY', function() {
    var mockedTarget = {
        offsetLeft: 0,
        offsetTop: 0
    };
    var mockedEvent = {
        target: mockedTarget,
        currentTarget: mockedTarget,
        offsetX: 80,  // 2 times grid size
        offsetY: 40
    };
    scope.updatePosition(mockedEvent);
    ok(scope.actualX === 2);
    ok(scope.actualY === 1);
});
