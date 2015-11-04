(function ($) {
    'use strict';
    var connections = [
        {
            app: 'back_office',
            model: 'backofficeasset',
            conf: [
                {
                    src: 'user',
                    func: function($form, $src, val) {
                        var $owner = $('[name=owner]', $form);
                        if ($owner.val() === '') {
                            $owner.val(val);
                        }
                        $('[name=status]', $form).val(2); // change to in progress
                    }
                }
            ]
        }
    ];
    $(document).ready(function () {
        connections.forEach(function (value) {
            var $form = $('.app-' + value.app + ' #' + value.model + '_form');
            value.conf.forEach(function (conf) {
                $('[name=' + conf.src + ']', $form).on('input change', function(event) {
                    conf.func($form, $(this), event.val);
                });
            });
        });
    });
})(ralph.jQuery);
