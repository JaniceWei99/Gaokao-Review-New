var api = require('../../services/api');
var app = getApp();

Page({
  data: {
    suggestions: [],
    summary: '',
    loading: true,
    studentId: null
  },

  onLoad: function() {
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    this.setData({ studentId: studentId });
    this.loadSuggestions();
  },

  loadSuggestions: function() {
    var that = this;
    var studentId = that.data.studentId;

    that.setData({ loading: true });

    api.get('/api/students/' + studentId + '/ai/action-suggestions').then(function(res) {
      that.setData({
        suggestions: res.suggestions || [],
        summary: res.summary || '',
        loading: false
      });
    }).catch(function(err) {
      console.warn('[AI Suggestions] load error:', err);
      that.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    });
  },

  onRefresh: function() {
    this.loadSuggestions();
  },

  onSuggestionTap: function(e) {
    var idx = e.currentTarget.dataset.index;
    var suggestion = this.data.suggestions[idx];
    if (!suggestion) return;

    wx.showModal({
      title: suggestion.title,
      content: suggestion.description,
      showCancel: false,
      confirmText: '知道了'
    });
  }
});
