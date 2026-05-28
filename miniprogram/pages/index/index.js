var api = require('../../services/api');
var dateUtil = require('../../utils/date');
var app = getApp();

Page({
  data: {
    quote: '',
    quoteAuthor: '',
    isFavorited: false,
    nearestCountdown: null,
    gaokaoCountdown: null,
    activeActionCard: null,
    upcomingMilestones: [],
    errorNotesSummary: { total: 0, top_subject: null, top_count: 0 },
    growthRecordsCount: 0,
    subscription: null,
    showSubscribeGuide: false,
    showDesktopGuide: false,
    personalizedQuote: null,
    loading: true
  },

  onLoad: function() {
    this.loadDashboard();
    this.checkSubscribeGuide();
    this.checkDesktopGuide();
  },

  onShow: function() {
    if (app.isLoggedIn() && app.getCurrentStudentId()) {
      this.loadDashboard();
    }
  },

  onPullDownRefresh: function() {
    var that = this;
    that.loadDashboard().finally(function() {
      wx.stopPullDownRefresh();
    });
  },

  loadDashboard: function() {
    var that = this;

    if (!app.isLoggedIn()) {
      that.setData({ loading: false });
      return Promise.resolve();
    }

    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      that.setData({ loading: false });
      return Promise.resolve();
    }

    that.setData({ loading: true });

    return api.get('/api/students/' + studentId + '/dashboard').then(function(res) {
      var data = res || {};
      var quoteData = data.today_quote || {};
      var countdowns = data.countdowns || {};
      var quote = quoteData.quote || {};

      var nearestCountdown = countdowns.nearest_exam || null;
      var gaokaoCountdown = countdowns.gaokao || null;

      var upcomingMilestones = (data.upcoming_milestones || []).map(function(item) {
        return {
          id: item.id,
          title: item.title,
          event_date: item.event_date,
          days_remaining: item.days_remaining,
          date_display: dateUtil.formatRelative(item.event_date),
          category: item.category
        };
      });

      that.setData({
        quote: quote.content || '每一天的努力，都是在为未来铺路。',
        quoteAuthor: quote.author ? ('— ' + quote.author) : '',
        isFavorited: quoteData.is_favorited || false,
        nearestCountdown: nearestCountdown,
        gaokaoCountdown: gaokaoCountdown,
        activeActionCard: data.active_action_card || null,
        upcomingMilestones: upcomingMilestones,
        errorNotesSummary: data.error_notes_summary || { total: 0, top_subject: null, top_count: 0 },
        growthRecordsCount: data.growth_records_count || 0,
        subscription: data.subscription || null,
        loading: false
      });

      that.checkDesktopGuide();
    }).catch(function(err) {
      console.warn('[Home] loadDashboard error:', err);
      that.setData({ loading: false });
    });
  },

  checkSubscribeGuide: function() {
    var that = this;
    var shown = wx.getStorageSync('subscribe_guide_shown');
    if (shown) return;

    if (!app.isLoggedIn()) return;

    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    api.get('/api/students/' + studentId + '/milestones?current=true&limit=3').then(function(res) {
      var milestones = res.milestones || [];
      var hasUpcoming = milestones.some(function(m) {
        return m.days_remaining <= 15;
      });

      if (hasUpcoming) {
        that.setData({ showSubscribeGuide: true });
      }
    }).catch(function() {});
  },

  onRequestSubscribe: function() {
    var that = this;
    wx.requestSubscribeMessage({
      tmplIds: [app.globalData.subscribeMilestoneTemplateId || ''],
      success: function(res) {
        wx.setStorageSync('subscribe_guide_shown', true);
        that.setData({ showSubscribeGuide: false });
        wx.showToast({ title: '订阅成功', icon: 'success' });
      },
      fail: function() {
        that.setData({ showSubscribeGuide: false });
      },
      complete: function() {
        wx.setStorageSync('subscribe_guide_shown', true);
      }
    });
  },

  onDismissSubscribe: function() {
    wx.setStorageSync('subscribe_guide_shown', true);
    this.setData({ showSubscribeGuide: false });
  },

  checkDesktopGuide: function() {
    var shown = wx.getStorageSync('desktop_guide_shown');
    if (shown) return;

    var sub = this.data.subscription;
    if (!sub) return;

    var plan = sub.plan || 'free';
    if (plan === 'free') return;

    if (typeof wx.addDesktopIcon !== 'function') return;

    this.setData({ showDesktopGuide: true });
  },

  onAddDesktop: function() {
    var that = this;
    wx.addDesktopIcon({
      success: function() {
        wx.showToast({ title: '已添加到桌面', icon: 'success' });
        wx.setStorageSync('desktop_guide_shown', true);
        that.setData({ showDesktopGuide: false });
      },
      fail: function() {
        wx.showToast({ title: '添加失败，可点击右上角手动添加', icon: 'none' });
        wx.setStorageSync('desktop_guide_shown', true);
        that.setData({ showDesktopGuide: false });
      }
    });
  },

  onDismissDesktop: function() {
    wx.setStorageSync('desktop_guide_shown', true);
    this.setData({ showDesktopGuide: false });
  },

  onToggleFavorite: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    var quoteData = that.data;
    if (!quoteData.quote) return;

    api.get('/api/quotes/daily', { student_id: studentId }).then(function(res) {
      var quote = (res && res.quote) || {};
      if (!quote.id) return;

      if (quoteData.isFavorited) {
        return api.del('/api/quotes/' + quote.id + '/favorite').then(function() {
          that.setData({ isFavorited: false });
          wx.showToast({ title: '已取消收藏', icon: 'none' });
        });
      } else {
        return api.post('/api/quotes/' + quote.id + '/favorite').then(function() {
          that.setData({ isFavorited: true });
          wx.showToast({ title: '已收藏', icon: 'success' });
        });
      }
    }).catch(function(err) {
      console.warn('[Home] favorite error:', err);
    });
  },

  onViewMilestones: function() {
    wx.navigateTo({ url: '/pages/milestones/timeline' });
  },

  onViewActionCard: function() {
    var card = this.data.activeActionCard;
    if (!card) return;

    var milestoneId = card.milestone_id;
    if (milestoneId) {
      wx.navigateTo({ url: '/pages/milestones/action-card?id=' + milestoneId });
    }
  },

  onNavigateTo: function(e) {
    var url = e.currentTarget.dataset.url;
    if (url) {
      wx.navigateTo({ url: url });
    }
  },

  onUpgradeToPremium: function() {
    wx.navigateTo({ url: '/pages/profile/subscription' });
  },

  onGenerateAIQuote: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    wx.showLoading({ title: '生成中...' });
    api.get('/api/students/' + studentId + '/ai/personalized-quote').then(function(res) {
      wx.hideLoading();
      that.setData({ personalizedQuote: res });
    }).catch(function(err) {
      wx.hideLoading();
      wx.showToast({ title: '生成失败', icon: 'none' });
    });
  }
});
