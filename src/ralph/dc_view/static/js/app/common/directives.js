(function(){
    'use strict';

    angular
        .module('common.directives', [])
        .directive('tooltip', ['$compile', function ($compile) {
            var template = '<i data-tooltip aria-haspopup="true" title="{{ tip }}" aria-hidden="true" class="has-tip fa fa-info-circle"></i><span class="show-for-sr">{{ tip }}</span>';
            return {
                restrict: 'E',
                transclude: true,
                compile: function(element, attrs, transclude) {
                    element.replaceWith(template);
                    return function(scope, element) {
                        Foundation.libs.tooltip.events(element);
                        var tip = Foundation.libs.tooltip.getTip(element);
                        transclude(scope, function(clone, scope) {
                            tip.html(clone);
                        });
                        $compile(tip.contents())(scope);
                    };
                }
            };
        }]);
})();
