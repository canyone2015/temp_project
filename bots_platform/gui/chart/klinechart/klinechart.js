// comment debug
var _log = console.log;
console.log = function () {
    this._last = [].slice.call(arguments);
    _log.apply(console, arguments);
};
console.last = function() {
    return this._last;
};

function isNumber(value) {
  return typeof value === 'number' && isFinite(value);
}

export default {
  template: "<div></div>",
  mounted() {
    setTimeout(() => {
      const imports = this.libraries.map((library) => import(window.path_prefix + library));
      Promise.allSettled(imports).then(() => {

        klinecharts.registerOverlay({
          name: 'lines',
          needDefaultPointFigure: true,
          needDefaultXAxisFigure: true,
          needDefaultYAxisFigure: true,
          totalStep: 1000,
          createPointFigures: ({ coordinates }) => {
            return [{
              type: 'line',
              attrs: { coordinates }
            }];
          }
        });

        klinecharts.registerOverlay({
          name: 'price_line',
          needDefaultPointFigure: true,
          needDefaultXAxisFigure: true,
          needDefaultYAxisFigure: true,
          totalStep: 2,
          createPointFigures: ({ coordinates, bounding, overlay, precision }) => {
            let text = '', align = 'right';
            if (overlay.extendData != null) {
              if (overlay.extendData.text != null) {
                text = overlay.extendData.text;
              }
              if (overlay.extendData.align != null) {
                align = overlay.extendData.align;
              }
            }
            const p = precision.price;
            const value = ((overlay.points)[0].value ?? 0).toFixed(p);
            return [
              {
                type: 'line',
                attrs: {
                  coordinates:
                    align == 'left'
                      ? [coordinates[0], { x: bounding.width, y: coordinates[0].y }]
                      : [{ x: 0, y: coordinates[0].y }, coordinates[0]]
                }
              },
              {
                type: 'text',
                ignoreEvent: true,
                attrs: {
                  x: coordinates[0].x,
                  y: coordinates[0].y,
                  text: text ? text : `${value}`,
                  align: align,
                  baseline: 'bottom',
                }
              }
            ];
          }
        });

        klinecharts.registerOverlay({
          name: 'marker',
          needDefaultPointFigure: true,
          needDefaultXAxisFigure: true,
          needDefaultYAxisFigure: true,
          totalStep: 2,
          createPointFigures: ({ coordinates, overlay }) => {
            let text = '';
            if (overlay.extendData != null) {
              if (overlay.extendData.text != null) {
                text = overlay.extendData.text;
              }
            }
            const startX = coordinates[0].x;
            const startY = coordinates[0].y;
            const lineEndY = startY - 50;
            const arrowEndY = lineEndY;
            return [
              {
                type: 'line',
                attrs: { coordinates: [{ x: startX, y: startY }, { x: startX, y: lineEndY }] },
              },
              {
                type: 'text',
                attrs: { x: startX, y: arrowEndY, text: text ?? '', align: 'center', baseline: 'bottom' },
                ignoreEvent: true
              }
            ];
          }
        });

        klinecharts.registerOverlay({
          name: 'percentage_change',
          needDefaultPointFigure: true,
          needDefaultXAxisFigure: true,
          needDefaultYAxisFigure: true,
          totalStep: 3,
          styles: { polygon: { color: 'rgba(22, 119, 255, 0.15)' } },
          createPointFigures: ({ coordinates, overlay, precision }) => {
            if (coordinates.length >= 2 && overlay.points.length >= 2) {
              const points = overlay.points;
              const data = this.chart._chartStore._dataList;
              const t1 = points[0].timestamp;
              const t2 = points[1].timestamp;
              const v1 = points[0].value;
              const v2 = points[1].value;
              if (v1 != 0 && v2 != 0) {
                const to_timedelta_string = function(t1, t2) {
                  if (!isNumber(t1) || !isNumber(t2)) {
                    return '';
                  }
                  let seconds = Math.floor((t2 - t1) / 1000);
                  let minutes = Math.floor(seconds / 60);
                  let hours = Math.floor(minutes / 60);
                  minutes = minutes % 60;
                  let days = Math.floor(hours / 24);
                  hours = hours % 24;
                  let s = '';
                  if (days > 0) s = s.concat(days + 'd');
                  if (hours > 0) s = s.concat((s.length > 0 ? ' ' : '') + hours + 'h');
                  if (minutes > 0) s = s.concat((s.length > 0 ? ' ' : '') + minutes + 'm');
                  return s;
                }
                let timedelta_str = to_timedelta_string(t1, t2);
                const y1 = coordinates[0].y;
                const y2 = coordinates[1].y;
                const x1 = coordinates[0].x;
                const x2 = coordinates[1].x;
                const percent_change = (v2 * 100 / v1 - 100).toFixed(3);
                const percent_change_str = percent_change >= 0 ? `+${percent_change}` : `-${Math.abs(percent_change)}`;
                let additional = [];
                if (isNumber(t1) && isNumber(t2) && t1 < t2) {
                  additional.push({
                    type: 'text',
                    ignoreEvent: true,
                    attrs: { x: x2, y: y1 + 10, text: timedelta_str, baseline: 'bottom' }
                  });
                }
                return [
                  {
                    type: 'polygon',
                    attrs: {
                      coordinates: [
                        coordinates[0], { x: coordinates[1].x, y: coordinates[0].y },
                        coordinates[1], { x: coordinates[0].x, y: coordinates[1].y }
                      ]
                    },
                    ignoreEvent: true,
                    styles: { style: 'stroke_fill' }
                  },
                  {
                    type: 'line',
                    attrs: {
                      coordinates: [
                        { x: coordinates[0].x, y: coordinates[0].y },
                        { x: coordinates[1].x, y: coordinates[1].y }
                      ]
                    },
                    styles: { style: 'stroke_fill' }
                  },
                  {
                    type: 'text',
                    ignoreEvent: true,
                    attrs: { x: x2, y: y2 + 10, text: `${percent_change_str}%`, baseline: 'bottom' }
                  },
                  ...additional
                ];
              }
            }
            return [];
          }
        });

        klinecharts.registerOverlay({
          name: 'risk_reward',
          totalStep: 5,
          needDefaultPointFigure: true,
          needDefaultXAxisFigure: false,
          needDefaultYAxisFigure: true,
          performEventMoveForDrawing: ({currentStep, points, performPoint}) => {
            switch (currentStep) {
              case 2:
                points[0].value = performPoint.value;
                break;
              case 3:
                points[1].timestamp = performPoint.timestamp;
                points[1].dataIndex = performPoint.dataIndex;
                break;
              case 4:
                points[1].timestamp = points[2].timestamp = performPoint.timestamp;
                points[1].dataIndex = points[2].dataIndex = performPoint.dataIndex;
                break;
            }
          },
          performEventPressedMove: ({points, performPointIndex, performPoint}) => {
            switch (performPointIndex) {
              case 0:
                points[1].value = performPoint.value;
                break;
              case 1:
                points[0].value = performPoint.value;
                points[2].timestamp = points[3].timestamp = performPoint.timestamp;
                points[2].dataIndex = points[3].dataIndex = performPoint.dataIndex;
                break;
              case 2:
                points[1].timestamp = points[3].timestamp = performPoint.timestamp;
                points[1].dataIndex = points[3].dataIndex = performPoint.dataIndex;
                break;
              case 3:
                points[1].timestamp = points[2].timestamp = performPoint.timestamp;
                points[1].dataIndex = points[2].dataIndex = performPoint.dataIndex;
                break;
            }
          },
          createPointFigures: ({coordinates, overlay}) => {
            const n = coordinates.length;
            if (n >= 2) {
              const line = {type: 'line', attrs: {coordinates}};
              if (n == 2) {
                return [line];
              }
              if (n >= 3) {
                const bottomRect = {
                  type: 'polygon',
                  attrs: {
                    coordinates: [
                      coordinates[0],
                      coordinates[1],
                      { x: coordinates[1].x, y: coordinates[2].y },
                      { x: coordinates[0].x, y: coordinates[2].y },
                    ],
                  },
                  styles: { style: 'fill', color: '#F4511E40' },
                };
                if (n == 3) {
                  return [bottomRect];
                }
                const topRect = {
                  type: 'polygon',
                  attrs: {
                    coordinates: [
                      coordinates[0],
                      coordinates[1],
                      { x: coordinates[1].x, y: coordinates[3].y },
                      { x: coordinates[0].x, y: coordinates[3].y },
                    ],
                  },
                  styles: { style: 'fill', color: '#7CB34240' },
                };
                let additional = [];
                const points = overlay.points;
                if (n >= 4 && points[1].value != 0) {
                  let tr1 = Math.abs(points[2].value / points[1].value - 1);
                  let tr2 = Math.abs(points[3].value / points[1].value - 1);
                  let reward = Math.floor(tr2 / tr1 * 100) / 100;
                  let reward_percents = Math.floor(tr2 * 1000) / 10;
                  let reward_percents_str = `+${reward_percents}%`;
                  additional.push({
                    type: 'text',
                    attrs: { x: coordinates[1].x, y: coordinates[3].y + 10, text: reward_percents_str, baseline: 'bottom' },
                    ignoreEvent: true
                  });
                  let rr_str = `Risk:Reward 1:${reward}`;
                  additional.push({
                    type: 'text',
                    attrs: { x: coordinates[1].x, y: coordinates[1].y, text: rr_str, baseline: 'bottom' },
                    ignoreEvent: true
                  });
                  let risk_percents = Math.floor(tr1 * 1000) / 10;
                  let risk_percents_str = `-${risk_percents}%`;
                  additional.push({
                    type: 'text',
                    attrs: { x: coordinates[1].x, y: coordinates[2].y + 10, text: risk_percents_str, baseline: 'bottom' },
                    ignoreEvent: true
                  });
                }
                return [bottomRect, topRect, ...additional];
              }
            }
          },
        });

        klinecharts.registerOverlay({
          name: 'buildup_drawdown',
          needDefaultPointFigure: true,
          needDefaultXAxisFigure: true,
          needDefaultYAxisFigure: true,
          totalStep: 3,
          styles: { polygon: { color: 'rgba(22, 119, 255, 0.15)' }, 'line': { size: 5 } },
          performEventMoveForDrawing: ({currentStep, points, performPoint}) => {
            switch (currentStep) {
              case 2:
                points[0].value = performPoint.value;
                points[1].value = performPoint.value;
                points[1].dataIndex = Math.max(points[0].dataIndex, performPoint.dataIndex);
                break;
            }
          },
          performEventPressedMove: ({points, performPointIndex, performPoint}) => {
            switch (performPointIndex) {
              case 0:
                points[1].value = performPoint.value;
                points[1].dataIndex = Math.max(points[1].dataIndex, performPoint.dataIndex);
                break;
              case 1:
                points[0].value = performPoint.value;
                points[1].dataIndex = Math.max(points[0].dataIndex, performPoint.dataIndex);
                break;
            }
          },
          createPointFigures: ({ coordinates, overlay, precision }) => {
            if (coordinates.length < 2) {
              return [];
            }
            if (overlay.points.length >= 2) {
              const points = overlay.points;
              const data = this.chart._chartStore._dataList;
              const p1t = Math.min(data.length - 1, Math.max(0, points[0].dataIndex));
              const p2t = Math.min(data.length - 1, Math.max(0, points[1].dataIndex));
              if (!(points[0].dataIndex >= data.length || points[1].dataIndex < 0) &&
                  0 <= p1t && p1t < data.length && 0 <= p2t && p2t < data.length) {
                const bu_r_min = data[p1t].open, bu_r_max = data[p2t].close, dd_r_min = data[p1t].high;
                let dd_r_max = data[p1t].low;
                for (let i = p1t; i <= p2t; ++i) {
                  if (dd_r_max > data[i].low) {
                    dd_r_max = data[i].low;
                  }
                }
                let additional = [];
                if (bu_r_min !== 0) {
                  const percent_change = (bu_r_max * 100 / bu_r_min - 100).toFixed(3);
                  const percent_change_str = `Buildup: ${percent_change}%`;
                  additional.push({
                    type: 'text',
                    ignoreEvent: true,
                    attrs: { x: coordinates[1].x, y: coordinates[1].y,
                             text: percent_change_str, baseline: 'bottom' }
                  });
                }
                if (dd_r_min !== 0) {
                  const percent_change = (dd_r_max * 100 / dd_r_min - 100).toFixed(3);
                  const percent_change_str = `Drawdown: ${percent_change}%`;
                  additional.push({
                    type: 'text',
                    ignoreEvent: true,
                    attrs: { x: coordinates[1].x, y: coordinates[1].y + 20,
                             text: percent_change_str, baseline: 'bottom' }
                  });
                }
                return [
                  {
                    type: 'line',
                    attrs: {
                      coordinates: [
                        { x: coordinates[0].x, y: coordinates[0].y },
                        { x: coordinates[1].x, y: coordinates[1].y }
                      ]
                    },
                    styles: { style: 'stroke_fill' }
                  },
                  ...additional
                ];
              }
            }
            return [{
              type: 'line',
              attrs: {
                coordinates: [
                  { x: coordinates[0].x, y: coordinates[0].y },
                  { x: coordinates[1].x, y: coordinates[1].y }
                ]
              },
              styles: { style: 'stroke_fill' }
            }];
          }
        });

        klinecharts.registerOverlay({
          name: 'buildup_drawdown_max',
          needDefaultPointFigure: true,
          needDefaultXAxisFigure: true,
          needDefaultYAxisFigure: true,
          totalStep: 3,
          styles: { polygon: { color: 'rgba(22, 119, 255, 0.15)' }, 'line': { size: 5 } },
          performEventMoveForDrawing: ({currentStep, points, performPoint}) => {
            switch (currentStep) {
              case 2:
                points[0].value = performPoint.value;
                points[1].value = performPoint.value;
                points[1].dataIndex = Math.max(points[0].dataIndex, performPoint.dataIndex);
                break;
            }
          },
          performEventPressedMove: ({points, performPointIndex, performPoint}) => {
            switch (performPointIndex) {
              case 0:
                points[1].value = performPoint.value;
                points[1].dataIndex = Math.max(points[1].dataIndex, performPoint.dataIndex);
                break;
              case 1:
                points[0].value = performPoint.value;
                points[1].dataIndex = Math.max(points[0].dataIndex, performPoint.dataIndex);
                break;
            }
          },
          createPointFigures: ({ coordinates, overlay, precision }) => {
            if (coordinates.length < 2) {
              return [];
            }
            if (overlay.points.length >= 2) {
              const points = overlay.points;
              const data = this.chart._chartStore._dataList;
              const p1t = Math.min(data.length - 1, Math.max(0, points[0].dataIndex));
              const p2t = Math.min(data.length - 1, Math.max(0, points[1].dataIndex));
              if (!(points[0].dataIndex >= data.length || points[1].dataIndex < 0) &&
                  0 <= p1t && p1t < data.length && 0 <= p2t && p2t < data.length) {
                let bu_r_max = 0, bu_r_min = 0;
                let bu_current_min = null, bu_max_after_min = null;
                let dd_r_max = 0, dd_r_min = 0;
                let dd_current_max = null, dd_min_after_max = null;
                for (let i = p1t; i <= p2t; ++i) {
                  if (bu_current_min == null || data[i].low < bu_current_min) {
                    bu_current_min = data[i].low;
                    bu_max_after_min = null;
                  }
                  if (bu_max_after_min == null || data[i].high > bu_max_after_min) {
                    bu_max_after_min = data[i].high;
                    if (bu_current_min !== 0 && (bu_r_min === 0 ||
                        bu_max_after_min / bu_current_min > bu_r_max / bu_r_min)) {
                      bu_r_max = bu_max_after_min;
                      bu_r_min = bu_current_min;
                    }
                  }
                  if (dd_current_max == null || data[i].high > dd_current_max) {
                    dd_current_max = data[i].high;
                    dd_min_after_max = null;
                  }
                  if (dd_min_after_max == null || data[i].low < dd_min_after_max) {
                    dd_min_after_max = data[i].low;
                    if (dd_min_after_max !== 0 && (dd_r_min === 0 ||
                        dd_current_max / dd_min_after_max > dd_r_max / dd_r_min)) {
                      dd_r_max = dd_current_max;
                      dd_r_min = dd_min_after_max;
                    }
                  }
                }
                let additional = [];
                if (bu_r_min !== 0) {
                  const percent_change = (bu_r_max * 100 / bu_r_min - 100).toFixed(3);
                  const percent_change_str = `Max buildup: ${percent_change}%`;
                  additional.push({
                    type: 'text',
                    ignoreEvent: true,
                    attrs: { x: coordinates[1].x, y: coordinates[1].y,
                             text: percent_change_str, baseline: 'bottom' }
                  });
                }
                if (dd_r_min !== 0) {
                  const percent_change = (dd_r_max * 100 / dd_r_min - 100).toFixed(3);
                  const percent_change_str = `Max drawdown: ${percent_change}%`;
                  additional.push({
                    type: 'text',
                    ignoreEvent: true,
                    attrs: { x: coordinates[1].x, y: coordinates[1].y + 20,
                             text: percent_change_str, baseline: 'bottom' }
                  });
                }
                return [
                  {
                    type: 'line',
                    attrs: {
                      coordinates: [
                        { x: coordinates[0].x, y: coordinates[0].y },
                        { x: coordinates[1].x, y: coordinates[1].y }
                      ]
                    },
                    styles: { style: 'stroke_fill' }
                  },
                  ...additional
                ];
              }
            }
            return [{
              type: 'line',
              attrs: {
                coordinates: [
                  { x: coordinates[0].x, y: coordinates[0].y },
                  { x: coordinates[1].x, y: coordinates[1].y }
                ]
              },
              styles: { style: 'stroke_fill' }
            }];
          }
        });

        klinecharts.registerOverlay({
          name: 'volume_profile',
          needDefaultPointFigure: true,
          needDefaultXAxisFigure: true,
          needDefaultYAxisFigure: true,
          totalStep: 5,
          styles: { polygon: { color: 'rgba(22, 119, 255, 0.15)' } },
          performEventMoveForDrawing: ({currentStep, points, performPoint}) => {
            switch (currentStep) {
              case 2:
                points[0].value = performPoint.value;
                points[1].dataIndex = Math.max(points[1].dataIndex, points[0].dataIndex);
                points[1].timestamp = Math.max(points[1].timestamp, points[0].timestamp);
                break;
              case 3:
                points[0].value = performPoint.value;
                points[1].value = performPoint.value;
                points[1].dataIndex = Math.max(points[1].dataIndex, points[0].dataIndex);
                points[2].dataIndex = Math.max(points[2].dataIndex, points[1].dataIndex);
                points[1].timestamp = Math.max(points[1].timestamp, points[0].timestamp);
                points[2].timestamp = Math.max(points[2].timestamp, points[1].timestamp);
                break;
              case 4:
                points[3].dataIndex = points[2].dataIndex;
                points[3].timestamp = points[2].timestamp;
                break;
            }
          },
          performEventPressedMove: ({points, performPointIndex, performPoint}) => {
            if (performPointIndex != 3) {
              let t = performPointIndex == 2 ? points[1].value : points[2].value;
              points[3].value = points[3].value - t + performPoint.value;
              points[0].value = performPoint.value;
              points[1].value = performPoint.value;
              points[2].value = performPoint.value;
              points[1].dataIndex = Math.max(points[1].dataIndex, points[0].dataIndex);
              points[2].dataIndex = Math.max(points[2].dataIndex, points[1].dataIndex);
              points[1].timestamp = Math.max(points[1].timestamp, points[0].timestamp);
              points[2].timestamp = Math.max(points[2].timestamp, points[1].timestamp);
            }
            points[3].dataIndex = points[2].dataIndex;
            points[3].timestamp = points[2].timestamp;
          },
          createPointFigures: ({ coordinates, overlay, precision, bounding }) => {
            let additional = [];
            if (coordinates.length == 0) {
              return additional;
            }
            additional.push({
              type: 'line',
              attrs: {
                coordinates: [
                  { x: coordinates[0].x, y: 0 },
                  { x: coordinates[0].x, y: bounding.height }
                ]
              },
              styles: { style: 'stroke_fill' }
            });
            if (coordinates.length == 1) {
              return additional;
            }
            additional.push({
              type: 'line',
              attrs: {
                coordinates: [
                  { x: coordinates[1].x, y: 0 },
                  { x: coordinates[1].x, y: bounding.height }
                ]
              },
              styles: { style: 'stroke_fill' }
            });
            if (coordinates.length == 2) {
              return additional;
            }
            additional.push({
              type: 'line',
              attrs: {
                coordinates: [
                  { x: coordinates[2].x, y: 0 },
                  { x: coordinates[2].x, y: bounding.height }
                ]
              },
              styles: { style: 'stroke_fill' }
            });
            if (overlay.points.length >= 4) {
              const points = overlay.points;
              const data = this.chart._chartStore._dataList;
              const p1t = Math.min(data.length - 1, Math.max(0, points[0].dataIndex));
              const p2t = Math.min(data.length - 1, Math.max(0, points[1].dataIndex));
              if (!(points[0].dataIndex >= data.length || points[1].dataIndex < 0 ||
                    points[1].dataIndex > points[2].dataIndex - 20)) {
                let high_max = null, low_min = null;
                for (let i = p1t; i <= p2t; ++i) {
                  if (high_max == null || high_max < data[i].high) {
                    high_max = data[i].high;
                  }
                  if (low_min == null || low_min > data[i].low) {
                    low_min = data[i].low;
                  }
                }
                const xy1 = this.chart.convertToPixel(
                  {timestamp: data[p1t].timestamp, value: low_min},
                  {paneId: 'candle_pane'}
                );
                const xy2 = this.chart.convertToPixel(
                  {timestamp: data[p2t].timestamp, value: high_max},
                  {paneId: 'candle_pane'}
                );
                let d = Math.abs(coordinates[3].y - coordinates[2].y);
                const n = Math.floor(Math.abs(xy2.y - xy1.y) / d);
                if (2 <= n && n <= 50) {
                  additional = [];
                  additional.push({
                    type: 'polygon',
                    attrs: {
                      coordinates: [
                        { x: coordinates[1].x, y: xy1.y },
                        { x: coordinates[2].x, y: xy1.y },
                        { x: coordinates[2].x, y: xy2.y },
                        { x: coordinates[1].x, y: xy2.y },
                      ]
                    },
                    ignoreEvent: true,
                    styles: { style: 'stroke_fill', color: '#121212' }
                  });
                  d = Math.abs(xy2.y - xy1.y) / n;
                  let volume_max = 0;
                  let volume_profile_arr = [];
                  for (let i = 0; i < n; ++i) {
                    let volume_green = 0, volume_red = 0;
                    const t_max = high_max - i * Math.abs(high_max - low_min) / n;
                    const t_min = high_max - (i + 1) * Math.abs(high_max - low_min) / n;
                    for (let j = p1t; j <= p2t; ++j) {
                      if (!(data[j].high < t_min || data[j].low > t_max)) {
                        let x_max = Math.min(t_max, data[j].high);
                        let x_min = Math.max(t_min, data[j].low);
                        let dv = data[j].volume;
                        const v1 = dv * (x_max - Math.max(x_min, Math.min(x_max, data[j].open)));
                        const v2 = dv * (Math.min(x_max, Math.max(x_min, data[j].close)) - x_min);
                        volume_green += v1;
                        volume_red += v2;
                      }
                    }
                    volume_max = Math.max(volume_max, volume_green + volume_red);
                    volume_profile_arr.push([volume_green, volume_red]);
                  }
                  for (let i = 0; i < n; ++i) {
                    volume_profile_arr[i][0] = volume_profile_arr[i][0] / volume_max;
                    volume_profile_arr[i][1] = volume_profile_arr[i][1] / volume_max;
                  }
                  for (let i = 0; i < n; ++i) {
                    const y1 = i * d + xy2.y;
                    const y2 = (i + 1) * d + xy2.y;
                    const x2 = coordinates[2].x;
                    const x1 = x2 - (volume_profile_arr[i][0] + volume_profile_arr[i][1]) * (coordinates[2].x - coordinates[1].x);
                    const x12 = x1 + Math.abs(volume_profile_arr[i][0] - volume_profile_arr[i][1]) * (coordinates[2].x - coordinates[1].x);
                    additional.push({
                      type: 'polygon',
                      attrs: {
                        coordinates: [
                          { x: x12, y: y1 }, { x: x2, y: y1 },
                          { x: x2, y: y2 }, { x: x12, y: y2 }
                        ]
                      },
                      ignoreEvent: true,
                      styles: { style: 'fill', color: '#fa9829FF' }
                    });
                    const color = (volume_profile_arr[i][0] > volume_profile_arr[i][1]) ? '#2DC08EFF' : '#F92855FF';
                    additional.push({
                      type: 'polygon',
                      attrs: {
                        coordinates: [
                          { x: x1, y: y1 }, { x: x12, y: y1 },
                          { x: x12, y: y2 }, { x: x1, y: y2 }
                        ]
                      },
                      ignoreEvent: true,
                      styles: { style: 'fill', color: color }
                    });
                  }
                  additional.push({
                    type: 'line',
                    attrs: {
                      coordinates: [
                        { x: coordinates[0].x, y: xy1.y },
                        { x: coordinates[0].x, y: xy2.y },
                      ]
                    },
                    styles: { style: 'stroke_fill' },
                  });
                  additional.push({
                    type: 'line',
                    attrs: {
                      coordinates: [
                        { x: coordinates[1].x, y: xy1.y },
                        { x: coordinates[1].x, y: xy2.y },
                      ]
                    },
                    styles: { style: 'stroke_fill' },
                  });
                  additional.push({
                    type: 'line',
                    attrs: {
                      coordinates: [
                        { x: coordinates[0].x, y: xy1.y },
                        { x: coordinates[2].x, y: xy1.y },
                      ]
                    },
                    styles: { style: 'stroke_fill' },
                  });
                  additional.push({
                    type: 'line',
                    attrs: {
                      coordinates: [
                        { x: coordinates[0].x, y: xy2.y },
                        { x: coordinates[2].x, y: xy2.y },
                      ]
                    },
                    styles: { style: 'stroke_fill' },
                  });
                }
              }
            }
            return additional;
          }
        });

        this.chart = klinecharts.init(this.$el);
        this.chart.createIndicator({ name: 'VOL', calcParams: [] }, false);
        this.applied_data = [];
        this.applied_theme = '';
        this.applied_style = '';
        this.update_chart();
        // console.log(this.chart);
      });
    }, 0); // NOTE: wait for window.path_prefix to be set in app.mounted()
  },
  beforeDestroy() {
    this.destroy_chart();
  },
  beforeUnmount() {
    this.destroy_chart();
  },
  methods: {
    add_overlay(overlay_data) {
      if (this.chart) {
        this.chart.createOverlay(overlay_data);
      }
    },
    remove_overlay(group_id) {
      if (this.chart) {
        this.chart.removeOverlay({
          'groupId': group_id,
        });
      }
    },
    update_chart() {
      if (this.chart) {
        if (this.options.baseTheme != null && this.options.baseTheme !== this.applied_theme) {
          this.chart.setStyles(this.options.baseTheme);
          this.applied_theme = this.options.baseTheme;
        }
        const options_styles = (this.options.styles != null) ? JSON.stringify(this.options.styles) : "";
        if (options_styles !== this.applied_style) {
          this.chart.setStyles(this.options.styles);
          this.applied_style = options_styles;
        }
        if (this.options.timezone != null) {
          this.chart.setTimezone(this.options.timezone);
        }
        if (this.options.locale != null) {
          this.chart.setLocale(this.options.locale);
        }
        if (this.options.price_precision != null) {
          let price_volume = this.chart.getPriceVolumePrecision();
          this.chart.setPriceVolumePrecision(this.options.price_precision, price_volume.volume);
        }
        if (this.options.volume_precision != null) {
          let price_volume = this.chart.getPriceVolumePrecision();
          this.chart.setPriceVolumePrecision(price_volume.price, this.options.volume_precision);
        }
        if (this.options.data != null) {
          let options_data_length = this.options.data.length;
          let applied_data_length = this.applied_data.length;
          if (applied_data_length === 0 || options_data_length < applied_data_length) {
            this.chart.clearData();
            this.applied_data = [];
            this.chart.applyMoreData(this.options.data);
          }
          else {
            let mismatch_found = false;
            for (let i = 0; i < applied_data_length - 1; ++i) {
              if (this.options.data[i].timestamp !== this.applied_data[i].timestamp ||
                  this.options.data[i].open !== this.applied_data[i].open           ||
                  this.options.data[i].high !== this.applied_data[i].high           ||
                  this.options.data[i].low !== this.applied_data[i].low             ||
                  this.options.data[i].close !== this.applied_data[i].close         ||
                  this.options.data[i].volume !== this.applied_data[i].volume       ){
                mismatch_found = true;
                break;
              }
            }
            if (mismatch_found) {
              this.chart.clearData();
              this.applied_data = [];
              this.chart.applyMoreData(this.options.data);
            }
            else {
              let adl1 = applied_data_length - 1;
              if (this.options.data[adl1].timestamp !== this.applied_data[adl1].timestamp) {
                this.chart.clearData();
                this.applied_data = [];
                this.chart.applyMoreData(this.options.data);
              }
              else {
                for (let i = Math.max(0, adl1); i < options_data_length; ++i) {
                  this.chart.updateData(this.options.data[i]);
                }
              }
            }
          }
          this.applied_data = this.options.data;
        }
        this.chart._xAxisPane.update(4);
      }
    },
    destroy_chart() {
      if (this.chart) {
        this.chart.destroy();
      }
    },
  },
  props: {
    libraries: Array,
    options: Object
  },
};
