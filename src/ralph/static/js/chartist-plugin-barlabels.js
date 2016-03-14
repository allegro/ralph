(function(window, document, Chartist) {
  'use strict';

  var defaultOptions = {
    labelClass: 'ct-label',
    labelOffset: {
      x: 0,
      y: 0
    },
    textAnchor: 'middle',
  };

  Chartist.plugins = Chartist.plugins || {};
  Chartist.plugins.ctBarLabels = function(options) {

    options = Chartist.extend({}, defaultOptions, options);

    return function ctBarLabels(chart) {
      if(chart instanceof Chartist.Bar) {
        chart.on('draw', function(data) {
          if(data.type === 'bar') {
            var value = 0;
            var position = {
              style: 'text-anchor: ' + options.textAnchor
            };
            if(chart.options.horizontalBars) {
              value = data.value.x;
              Chartist.extend(position, {
                x: data.x2 + options.labelOffset.x + 10,
                y: data.y1 + options.labelOffset.y + 5,
              });
            } else {
              value = data.value.y;
              Chartist.extend(position, {
                x: data.x2,
                y: data.y2 + options.labelOffset.y - 10,
              });
            }
            data.group.elem('text', position, options.labelClass).text(value);
          }
        });
      }
    };
  };

}(window, document, Chartist));
