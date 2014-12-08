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
    .filter('slugify', function(){
        return function(input) {
            return input
                .toLowerCase()
                .replace(/[^\w ]+/g,'')
                .replace(/ +/g,'-');
        };
    });
