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
    loading: false
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

    api.get('/api/students/' + studentId + '/exams').then(function(res) {
      var exams = res.exams || res.data || res || [];
      var trend = [];

      exams.forEach(function(e) {
        var score = (e.scores || []).find(function(s) {
          return s.subject_id === subjectId;
        });
        if (score) {
          trend.push({
            exam_name: e.name,
            exam_date: e.exam_date,
            date_short: dateUtil.formatShort(e.exam_date),
            score: score.score,
            max_score: score.max_score,
            rate: score.max_score > 0 ? Math.round(score.score / score.max_score * 100) : 0
          });
        }
      });

      trend.sort(function(a, b) {
        return a.exam_date > b.exam_date ? 1 : -1;
      });

      that.setData({
        trendData: trend,
        loading: false
      });
    }).catch(function() {
      that.setData({ loading: false });
    });
  }
});
