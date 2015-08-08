(function(){
    'use strict';

    angular
        .module('common.filters', [])
        .filter('range', function () {
            return function (input, total) {
                for (var i = 0; i < parseInt(total); i++) {
                    input.push(i);
                }
                return input;
            };
        })
        .filter('clean', function(){
            return function(input) {
                return input
                    .toLowerCase()
                    .replace('rack ','')
                    .replace(/^\s+|\s+$/g, '');
            };
        })
        .filter('slugify', function(){
            return function(input) {
                return input
                    .toLowerCase()
                    .replace(/[^\w ]+/g,'')
                    .replace(/ +/g,'-');
            };
        })
        .filter('remove_alfa', function(){
            return function(input) {
                return input
                    .replace(/[^\d.-]/g, '');
            };
        });
})();
