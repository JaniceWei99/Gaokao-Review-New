var app = getApp();

Page({
  data: {
    quote: '',
    quoteAuthor: '',
    milestones: [],
    canAddDesktop: false
  },

  onLoad: function() {
    this._loadPreview();
    this._checkDesktopSupport();
  },

  _loadPreview: function() {
    var that = this;
    var api = require('../../services/api');
    var studentId = app.getCurrentStudentId();

    if (!studentId) return;

    api.get('/api/students/' + studentId + '/dashboard').then(function(res) {
      var data = res || {};
      var quoteData = data.today_quote || {};
      var quote = quoteData.quote || {};
      var milestones = (data.upcoming_milestones || []).slice(0, 3);

      that.setData({
        quote: quote.content || '每一天的努力，都是在为未来铺路。',
        quoteAuthor: quote.author ? ('— ' + quote.author) : '',
        milestones: milestones.map(function(m) {
          return {
            title: m.title,
            days_remaining: m.days_remaining,
            event_date: m.event_date
          };
        })
      });
    }).catch(function(err) {
      console.warn('[Complete] loadPreview error:', err);
    });
  },

  _checkDesktopSupport: function() {
    var that = this;
    if (wx.addDesktopIcon) {
      that.setData({ canAddDesktop: true });
    }
  },

  onAddDesktop: function() {
    if (!this.data.canAddDesktop) {
      wx.showToast({ title: '当前版本不支持添加到桌面', icon: 'none' });
      return;
    }

    wx.addDesktopIcon({
      success: function() {
        wx.showToast({ title: '已添加到桌面', icon: 'success' });
      },
      fail: function() {
        wx.showToast({ title: '添加失败', icon: 'none' });
      }
    });
  },

  onEnterHome: function() {
    wx.reLaunch({ url: '/pages/index/index' });
  }
});
