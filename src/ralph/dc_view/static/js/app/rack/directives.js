(function(){
    'use strict';

    angular
        .module('rack.directives', [])
        .directive('rack', function () {
            return {
                restrict: 'E',
                scope: {
                    devices: '=',
                    pdus: '=',
                    side: '@',
                    info: '='
                },
                templateUrl: '/static/partials/rack/rack.html',
                link: function(scope, element) {
                    console.log("SCOPE", scope);

                    var $ = jQuery;

                    var REDIRECT_URL = "/data_center/datacenterasset/add/?rack={rack_id}&position={position}&orientation={orientation}";
                    var ORIENTATION_FRONT = 1;
                    var ORIENTATION_BACK = 2;

                    function build_url(templ, fields) {
                        var key, val, regEx;
                        Object.keys(fields).forEach(function(key) {
                            val = fields[key];
                            regEx = new RegExp("{" + key + "}", "gi");
                            templ = templ.replace(regEx, val);
                        });
                        return templ;
                    }

                    var $rack = $(element).find('div.rack');
                    var $devices = $rack.find('.devices');
                    var elemHtml = [
                        '<div class="insert-device-btn" title="Click with CTRL key pressed to open in new tab">',
                            '<i class="fa fa-plus"></i>',
                        '</div>'
                    ];
                    elemHtml = elemHtml.join("");

                    $devices.on('mouseover', function() {
                        var $device = $(this);
                        if($device.find(".insert-device-btn").length === 0) {
                            var buttonRef = $(elemHtml).appendTo($device);
                            buttonRef.click(function(e) {
                                var $btn = $(this);
                                var position = $btn.attr('data-current-position');
                                var orientation = (scope.side == 'front') ? ORIENTATION_FRONT : ORIENTATION_BACK;
                                gotoAssetWizard(scope.info.id, position, orientation, e.ctrlKey);
                            });
                        } else {
                            $device.find(".insert-device-btn").show();
                        }
                    })
                    .on('mousemove', function(event) {
                        var $device = $(this);
                        var $parent = $device.parents("div.rack");
                        var position_y = event.pageY - $device.offset().top;
                        var $btn = $device.find(".insert-device-btn");
                        var maxRows = scope.info.max_u_height;
                        var rowHeight = $parent.find(".listing-u").first().find(".position").first().outerHeight();
                        var rowId = Math.floor(position_y / rowHeight);
                        var rackSlotId = maxRows - rowId;
                        if(canAddAssetAt(rackSlotId)) {
                            var newTop = rowId * rowHeight;
                            $btn.attr('data-current-position', rackSlotId);
                            $btn.css({
                                top: newTop + 'px'
                            });
                        }
                    })
                    .on('mouseout', function(e) {
                        var $device = $(this);
                        var toElement = $(e.toElement || e.relatedTarget);

                        var isTargetDevice = (toElement.is(".device") || toElement.parents(".device").length > 0);
                        var hideCondition = (toElement.parents(".devices").length === 0) || isTargetDevice;
                        if(hideCondition) {
                            $device.find(".insert-device-btn").hide();
                        }
                    });

                    function gotoAssetWizard(rack_id, position, orientation, is_ctrl) {
                        var url = build_url(REDIRECT_URL, {
                            rack_id: rack_id,
                            position: position,
                            orientation: orientation

                        });
                        if(!is_ctrl) {
                            location.href = url;
                        } else {
                            window.open(url);
                        }
                    }

                    function canAddAssetAt(y) {
                        if(y < 0 || y > scope.info.max_u_height) {
                            return false;
                        }
                        var can = true;
                        angular.forEach(scope.devices, function(device) {
                            var devPosition = device.position || scope.info.max_u_height;
                            var devHeight = device.height || 1;
                            var deviceMaxRow = devPosition + devHeight;
                            var i;
                            for(i = devPosition; i < deviceMaxRow; i += 1) {
                                if(i == y) {
                                    can = false;
                                    return false;
                                }
                            }
                        });
                        return can;
                    }
                }
            };
        })
        .directive('deviceItem', function () {
            return {
                restrict: 'E',
                scope: {
                    device: '=',
                    side: '='
                },
                templateUrl: '/static/partials/rack/device_item.html',
                link: function(scope) {
                    scope.setActiveItem = function(item) {
                        item.active = true;
                        scope.$emit('change_active_item', item);
                    };
                    scope.setActiveSlot = function(slot) {
                        scope.$emit('change_active_slot', slot);
                    };
                    scope.getLayout = function() {
                        return scope.device[scope.side + '_layout'];
                    };
                }
            };
        })
        .directive('listing', function () {
            return {
                restrict: 'E',
                templateUrl: '/static/partials/rack/listing.html',
                link: function (scope) {
                    scope.u_range = [];
                    scope.$on('change_active_item', function(event, item){
                        scope.u_range = [];
                        if (typeof item !== 'undefined' && item !== null) {
                            var itemHeight = 1;     // for accessories...
                            if (typeof(item.height) !== 'undefined') {
                                itemHeight = item.height;
                            }
                            for (var i = item.position; i <= item.position+itemHeight-1; i++) {
                                scope.u_range.push(i);
                            }
                        }
                    });
                }
            };
        })
        .directive('pduItem', function () {
            return {
                restrict: 'E',
                scope: {
                    pdu: '='
                },
                templateUrl: '/static/partials/rack/pdu_item.html',
                link: function(scope) {
                    scope.setActiveItem = function(item) {
                        scope.$emit('change_active_item', item);
                    };
                    scope.setActiveSlot = function(slot) {
                        scope.$emit('change_active_slot', slot);
                    };
                }
            };
        });
})();
