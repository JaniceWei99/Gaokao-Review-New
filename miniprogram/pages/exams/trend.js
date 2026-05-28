var api = require('../../services/api');
var dateUtil = require('../../utils/date');
var app = getApp();

Page({
  data: {
    subjectId: '',
    subjectOptions: [
      { key: 'chinese', label: '语文' },
      { key: 'math', label: '数学' },
      { key: 'english', label: '英语' },
      { key: 'physics', label: '物理' },
      { key: 'chemistry', label: '化学' },
      { key: 'biology', label: '生物' },
      { key: 'politics', label: '政治' },
      { key: 'history', label: '历史' },
      { key: 'geography', label: '地理' }
    ],
    subjectIndex: -1,
    trendData: [],
    loading: false,
    chartPoints: [],
    chartLabels: [],
    chartMin: 0,
    chartMax: 100,
    trendDirection: '',
    trendDelta: 0,
    avgRate: 0,
    bestRate: 0
  },

  onSubjectChange: function(e) {
    var idx = parseInt(e.detail.value);
    var subjectId = this.data.subjectOptions[idx].key;
    this.setData({ subjectIndex: idx, subjectId: subjectId });
    this.loadTrend(subjectId);
  },

  loadTrend: function(subjectId) {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId || !subjectId) return;

    that.setData({ loading: true });

    api.get('/api/students/' + studentId + '/exams/trend', {
      subject_id: subjectId
    }).then(function(res) {
      var points = res.data_points || [];
      if (points.length === 0) {
        that.setData({ trendData: [], loading: false });
        return;
      }

      var rates = points.map(function(p) { return p.rate; });
      var minRate = Math.min.apply(null, rates);
      var maxRate = Math.max.apply(null, rates);
      var chartMin = Math.max(0, Math.floor((minRate - 10) / 10) * 10);
      var chartMax = Math.min(100, Math.ceil((maxRate + 10) / 10) * 10);

      var sum = rates.reduce(function(a, b) { return a + b; }, 0);
      var avgRate = Math.round(sum / rates.length);
      var bestRate = maxRate;

      var trendDirection = '';
      var trendDelta = 0;
      if (rates.length >= 2) {
        var last = rates[rates.length - 1];
        var prev = rates[rates.length - 2];
        trendDelta = last - prev;
        if (trendDelta > 0) trendDirection = 'up';
        else if (trendDelta < 0) trendDirection = 'down';
        else trendDirection = 'flat';
      }

      var trendData = points.map(function(p) {
        return {
          exam_name: p.exam_name,
          exam_date: p.exam_date,
          date_short: dateUtil.formatShort(p.exam_date),
          score: p.score,
          max_score: p.max_score,
          rate: p.rate
        };
      });

      that.setData({
        trendData: trendData,
        chartPoints: rates,
        chartLabels: points.map(function(p) { return dateUtil.formatShort(p.exam_date); }),
        chartMin: chartMin,
        chartMax: chartMax,
        trendDirection: trendDirection,
        trendDelta: trendDelta,
        avgRate: avgRate,
        bestRate: bestRate,
        loading: false
      });

      that.drawChart();
    }).catch(function() {
      that.setData({ loading: false });
    });
  },

  drawChart: function() {
    var that = this;
    var points = that.data.chartPoints;
    if (points.length === 0) return;

    var query = wx.createSelectorQuery();
    query.select('#trendCanvas').fields({ node: true, size: true }).exec(function(res) {
      if (!res || !res[0]) return;

      var canvas = res[0].node;
      var ctx = canvas.getContext('2d');
      var dpr = wx.getWindowInfo().pixelRatio;
      var width = res[0].width;
      var height = res[0].height;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);

      var padding = { top: 20, right: 20, bottom: 30, left: 40 };
      var chartW = width - padding.left - padding.right;
      var chartH = height - padding.top - padding.bottom;

      var chartMin = that.data.chartMin;
      var chartMax = that.data.chartMax;
      var range = chartMax - chartMin;
      if (range === 0) range = 100;

      ctx.clearRect(0, 0, width, height);

      var gridLines = 5;
      ctx.strokeStyle = '#e8e8e8';
      ctx.lineWidth = 0.5;
      ctx.font = '10px sans-serif';
      ctx.fillStyle = '#999';
      ctx.textAlign = 'right';

      for (var i = 0; i <= gridLines; i++) {
        var yVal = chartMin + (range / gridLines) * i;
        var y = padding.top + chartH - (chartH * (yVal - chartMin) / range);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartW, y);
        ctx.stroke();
        ctx.fillText(Math.round(yVal) + '%', padding.left - 6, y + 3);
      }

      var step = chartW / (points.length - 1 || 1);
      var coords = points.map(function(p, idx) {
        return {
          x: padding.left + step * idx,
          y: padding.top + chartH - (chartH * (p - chartMin) / range)
        };
      });

      ctx.beginPath();
      ctx.strokeStyle = '#4a90d9';
      ctx.lineWidth = 2;
      ctx.lineJoin = 'round';
      coords.forEach(function(c, idx) {
        if (idx === 0) ctx.moveTo(c.x, c.y);
        else ctx.lineTo(c.x, c.y);
      });
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(coords[0].x, padding.top + chartH);
      coords.forEach(function(c) {
        ctx.lineTo(c.x, c.y);
      });
      ctx.lineTo(coords[coords.length - 1].x, padding.top + chartH);
      ctx.closePath();
      var grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
      grad.addColorStop(0, 'rgba(74, 144, 217, 0.3)');
      grad.addColorStop(1, 'rgba(74, 144, 217, 0.02)');
      ctx.fillStyle = grad;
      ctx.fill();

      coords.forEach(function(c, idx) {
        ctx.beginPath();
        ctx.arc(c.x, c.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#4a90d9';
        ctx.fill();
        ctx.beginPath();
        ctx.arc(c.x, c.y, 2, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.fill();
      });

      ctx.fillStyle = '#999';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      that.data.chartLabels.forEach(function(label, idx) {
        if (points.length <= 8 || idx % 2 === 0) {
          ctx.fillText(label, coords[idx].x, padding.top + chartH + 16);
        }
      });
    });
  }
});
