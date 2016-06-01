var serviceLocator = angular.injector(['ng', 'serverRoomVisualizationApp']);
var $controllers = serviceLocator.get('$controller');
var scope = {};
var serverRoomMock = {
    rack_set: []
};
var rackModel;

QUnit.module('Server Room controllers', {
    setup: function () {
        scope = serviceLocator.get('$rootScope').$new();
        rackModel = serviceLocator.get('RackModel');
        $controllers('ServerRoomController', {$scope: scope, server_room: serverRoomMock, RackModel: rackModel});
    }
});

test('newRack should add rack to rack_set', function(){
    ok(scope.server_room.rack_set.length === 0);
    scope.newRack(1, 1);
    ok(scope.server_room.rack_set.length === 1);
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
