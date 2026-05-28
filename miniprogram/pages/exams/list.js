var api = require('../../services/api');
var dateUtil = require('../../utils/date');
var app = getApp();

Page({
  data: {
    exams: [],
    loading: true
  },

  onLoad: function() {
    this.loadExams();
  },

  onPullDownRefresh: function() {
    var that = this;
    this.loadExams().then(function() {
      wx.stopPullDownRefresh();
    });
  },

  loadExams: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      that.setData({ loading: false });
      return Promise.resolve();
    }

    return api.get('/api/students/' + studentId + '/exams').then(function(res) {
      var exams = (res.exams || res.data || res || []).map(function(e) {
        e.date_display = dateUtil.formatDate(e.exam_date);
        e.type_label = that.getTypeLabel(e.exam_type);
        if (e.scores && e.scores.length > 0) {
          var total = 0;
          var maxTotal = 0;
          e.scores.forEach(function(s) {
            total += s.score;
            maxTotal += s.max_score;
          });
          e.total_score = total;
          e.max_total = maxTotal;
          e.rate = maxTotal > 0 ? Math.round(total / maxTotal * 100) : 0;
        }
        return e;
      });

      that.setData({
        exams: exams,
        loading: false
      });
    }).catch(function(err) {
      console.warn('[Exams] load error:', err);
      that.setData({ loading: false });
    });
  },

  getTypeLabel: function(type) {
    var map = {
      monthly: '月考',
      midterm: '期中',
      final: '期末',
      mock: '模考',
      other: '其他'
    };
    return map[type] || type;
  },

  onDeleteExam: function(e) {
    var that = this;
    var examId = e.currentTarget.dataset.id;
    var studentId = app.getCurrentStudentId();

    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除这条考试记录吗？',
      success: function(res) {
        if (res.confirm) {
          api.del('/api/students/' + studentId + '/exams/' + examId).then(function() {
            wx.showToast({ title: '已删除', icon: 'success' });
            that.loadExams();
          }).catch(function(err) {
            wx.showToast({ title: err.message || '删除失败', icon: 'none' });
          });
        }
      }
    });
  },

  onAddExam: function() {
    wx.navigateTo({ url: '/pages/exams/add' });
  }
});
