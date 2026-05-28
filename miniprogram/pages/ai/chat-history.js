var api = require('../../services/api');
var app = getApp();

Page({
  data: {
    sessions: [],
    loading: true,
    studentId: null
  },

  onLoad: function(options) {
    var studentId = options.student_id || app.getCurrentStudentId();
    if (!studentId) return;
    this.setData({ studentId: studentId });
    this.loadSessions();
  },

  loadSessions: function() {
    var that = this;
    var studentId = that.data.studentId;

    api.get('/api/students/' + studentId + '/ai-chat/sessions').then(function(res) {
      that.setData({
        sessions: res.sessions || [],
        loading: false
      });
    }).catch(function(err) {
      console.warn('[Chat History] load error:', err);
      that.setData({ loading: false });
    });
  },

  onSessionTap: function(e) {
    var sessionId = e.currentTarget.dataset.id;
    var studentId = this.data.studentId;
    wx.navigateTo({ url: '/pages/ai/chat?session_id=' + sessionId + '&student_id=' + studentId });
  },

  onDeleteSession: function(e) {
    var that = this;
    var sessionId = e.currentTarget.dataset.id;
    var studentId = that.data.studentId;

    wx.showModal({
      title: '删除对话',
      content: '确定删除这段对话记录吗？',
      success: function(res) {
        if (res.confirm) {
          api.del('/api/students/' + studentId + '/ai-chat/sessions/' + sessionId).then(function() {
            that.loadSessions();
          });
        }
      }
    });
  },

  onNewChat: function() {
    var studentId = this.data.studentId;
    wx.navigateTo({ url: '/pages/ai/chat?student_id=' + studentId });
  }
});
