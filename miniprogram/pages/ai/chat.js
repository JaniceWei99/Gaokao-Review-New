var api = require('../../services/api');
var permission = require('../../utils/permission');
var app = getApp();

Page({
  data: {
    messages: [],
    inputText: '',
    sessionId: null,
    loading: false,
    remainingChats: 10,
    subscription: null,
    showUpgradeModal: false,
    scrollToView: ''
  },

  onLoad: function(options) {
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    this.setData({ studentId: studentId });

    if (options.session_id) {
      this.setData({ sessionId: options.session_id });
      this.loadSessionMessages(options.session_id);
    }

    this.checkSubscription();
  },

  checkSubscription: function() {
    var that = this;
    var studentId = that.data.studentId;
    if (!studentId) return;

    api.get('/api/students/' + studentId + '/dashboard').then(function(res) {
      var sub = res.subscription || {};
      that.setData({ subscription: sub });

      if (sub.plan !== 'premium') {
        that.setData({ showUpgradeModal: true });
      }
    }).catch(function() {});
  },

  loadSessionMessages: function(sessionId) {
    var that = this;
    var studentId = that.data.studentId;

    api.get('/api/students/' + studentId + '/ai-chat/sessions/' + sessionId).then(function(res) {
      var messages = (res.messages || []).map(function(m) {
        return {
          id: m.id,
          role: m.role,
          content: m.content,
          time: that.formatTime(m.created_at)
        };
      });
      that.setData({ messages: messages });
      that.scrollToBottom();
    }).catch(function(err) {
      console.warn('[AI Chat] load messages error:', err);
    });
  },

  onInputChange: function(e) {
    this.setData({ inputText: e.detail.value });
  },

  sendMessage: function() {
    var that = this;
    var text = that.data.inputText.trim();
    if (!text) return;
    if (that.data.loading) return;

    var sub = that.data.subscription;
    if (!sub || sub.plan !== 'premium') {
      that.setData({ showUpgradeModal: true });
      return;
    }

    var userMsg = {
      id: 'temp_' + Date.now(),
      role: 'user',
      content: text,
      time: that.formatTime(new Date().toISOString())
    };

    that.setData({
      messages: that.data.messages.concat([userMsg]),
      inputText: '',
      loading: true
    });
    that.scrollToBottom();

    var studentId = that.data.studentId;
    var body = {
      message: text,
      session_id: that.data.sessionId || null
    };

    api.post('/api/students/' + studentId + '/ai-chat', body).then(function(res) {
      var aiMsg = {
        id: res.id || 'ai_' + Date.now(),
        role: 'assistant',
        content: res.content,
        time: that.formatTime(new Date().toISOString())
      };

      that.setData({
        messages: that.data.messages.concat([aiMsg]),
        sessionId: res.session_id || that.data.sessionId,
        remainingChats: res.remaining_chats || 0,
        loading: false
      });
      that.scrollToBottom();
    }).catch(function(err) {
      console.warn('[AI Chat] send error:', err);
      var errMsg = {
        id: 'err_' + Date.now(),
        role: 'assistant',
        content: '抱歉，AI顾问暂时无法回复，请稍后再试。',
        time: that.formatTime(new Date().toISOString())
      };
      that.setData({
        messages: that.data.messages.concat([errMsg]),
        loading: false
      });
      that.scrollToBottom();
    });
  },

  onUpgradeTap: function() {
    wx.navigateTo({ url: '/pages/profile/subscription' });
  },

  onCloseUpgrade: function() {
    this.setData({ showUpgradeModal: false });
    wx.navigateBack();
  },

  onViewHistory: function() {
    var studentId = this.data.studentId;
    wx.navigateTo({ url: '/pages/ai/chat-history?student_id=' + studentId });
  },

  scrollToBottom: function() {
    var that = this;
    setTimeout(function() {
      that.setData({ scrollToView: 'msg-bottom' });
    }, 100);
  },

  formatTime: function(isoStr) {
    if (!isoStr) return '';
    try {
      var d = new Date(isoStr);
      var h = d.getHours().toString().padStart(2, '0');
      var m = d.getMinutes().toString().padStart(2, '0');
      return h + ':' + m;
    } catch (e) {
      return '';
    }
  }
});
