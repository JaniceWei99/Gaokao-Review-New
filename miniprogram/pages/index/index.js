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
    loading: true
  },

  onLoad: function() {
    this.loadDashboard();
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
    }).catch(function(err) {
      console.warn('[Home] loadDashboard error:', err);
      that.setData({ loading: false });
    });
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
    if (!card || !card.id) return;
    wx.navigateTo({ url: '/pages/milestones/action-card?id=' + card.id });
  },

  onNavigateTo: function(e) {
    var url = e.currentTarget.dataset.url;
    if (url) {
      wx.navigateTo({ url: url });
    }
  }
});
