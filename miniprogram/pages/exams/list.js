var api = require('../../services/api');
var storage = require('../../services/storage');
var dateUtil = require('../../utils/date');
var app = getApp();

var SUBJECT_LABELS = {
  chinese: '语文', math: '数学', english: '英语',
  physics: '物理', chemistry: '化学', biology: '生物',
  politics: '政治', history: '历史', geography: '地理'
};

var TYPE_LABELS = {
  monthly: '月考', midterm: '期中', final: '期末', mock: '模考', other: '其他'
};

Page({
  data: {
    exams: [],
    loading: true,
    source: 'local',
    isLoggedIn: false
  },

  onLoad: function() {
    this.loadExams();
  },

  onShow: function() {
    this.loadExams();
  },

  onPullDownRefresh: function() {
    var that = this;
    this.loadExamsFromCloud().then(function() {
      wx.stopPullDownRefresh();
    });
  },

  loadExams: function() {
    var local = storage.getExams();
    if (local.length > 0) {
      this.setData({
        exams: this.processExams(local),
        loading: false,
        source: 'local',
        isLoggedIn: app.isLoggedIn()
      });
    } else {
      this.setData({ loading: false, isLoggedIn: app.isLoggedIn() });
    }

    if (app.isLoggedIn()) {
      this.loadExamsFromCloud();
    }
  },

  loadExamsFromCloud: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      return Promise.resolve();
    }

    return api.get('/api/students/' + studentId + '/exams').then(function(res) {
      var cloud = (res.exams || res.data || res || []);
      if (cloud.length > 0) {
        cloud.forEach(function(e) {
          storage.saveExam({
            id: e.id,
            name: e.name || e.exam_name || '',
            exam_type: e.exam_type || 'other',
            exam_date: e.exam_date || '',
            scores: e.scores || []
          });
        });
      }
      var merged = storage.getExams();
      that.setData({
        exams: that.processExams(merged),
        loading: false,
        source: cloud.length > 0 ? 'cloud' : 'local',
        isLoggedIn: app.isLoggedIn()
      });
    }).catch(function(err) {
      console.warn('[Exams] cloud load error:', err);
    });
  },

  processExams: function(exams) {
    var that = this;
    return exams.map(function(e) {
      var processed = {
        id: e.id,
        name: e.name || e.exam_name || '',
        exam_type: e.exam_type || 'other',
        exam_date: e.exam_date || '',
        date_display: dateUtil.formatDate(e.exam_date),
        type_label: that.getTypeLabel(e.exam_type || 'other'),
        scores: (e.scores || []).map(function(s) {
          return {
            subject_id: s.subject_id,
            subject_name: s.subject_name || SUBJECT_LABELS[s.subject_id] || s.subject_id,
            score: s.score || 0,
            max_score: s.max_score || 150
          };
        })
      };

      if (processed.scores.length > 0) {
        var total = 0;
        var maxTotal = 0;
        processed.scores.forEach(function(s) {
          total += s.score;
          maxTotal += s.max_score;
        });
        processed.total_score = total;
        processed.max_total = maxTotal;
        processed.rate = maxTotal > 0 ? Math.round(total / maxTotal * 100) : 0;
      } else {
        processed.total_score = 0;
        processed.max_total = 0;
        processed.rate = 0;
      }
      return processed;
    });
  },

  getTypeLabel: function(type) {
    return TYPE_LABELS[type] || type;
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
          storage.deleteExam(examId);
          var remaining = storage.getExams();
          that.setData({
            exams: that.processExams(remaining)
          });
          wx.showToast({ title: '已删除', icon: 'success' });

          if (app.isLoggedIn() && studentId) {
            api.del('/api/students/' + studentId + '/exams/' + examId).catch(function() {});
          }
        }
      }
    });
  },

  onAddExam: function() {
    wx.navigateTo({ url: '/pages/exams/add' });
  }
});
