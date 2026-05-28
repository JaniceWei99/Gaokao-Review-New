var api = require('../../services/api');
var dateUtil = require('../../utils/date');
var app = getApp();

Page({
  data: {
    milestones: [],
    loading: true,
    showPast: false
  },

  onLoad: function() {
    this.loadMilestones();
  },

  onPullDownRefresh: function() {
    var that = this;
    this.loadMilestones().then(function() {
      wx.stopPullDownRefresh();
    });
  },

  loadMilestones: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      that.setData({ loading: false });
      return Promise.resolve();
    }

    return api.get('/api/students/' + studentId + '/milestones').then(function(res) {
      var list = (res.milestones || res.data || res || []).map(function(item) {
        var days = dateUtil.daysUntil(item.event_date);
        return {
          id: item.id,
          name: item.name,
          event_date: item.event_date,
          date_display: dateUtil.formatDate(item.event_date),
          relative: dateUtil.formatRelative(item.event_date),
          days_away: days,
          is_past: days < 0,
          is_today: days === 0,
          type: item.type || 'system',
          action_card: item.action_card || null
        };
      });

      that.setData({
        milestones: list,
        loading: false
      });
    }).catch(function(err) {
      console.warn('[Milestones] load error:', err);
      that.setData({ loading: false });
    });
  },

  onTogglePast: function() {
    this.setData({ showPast: !this.data.showPast });
  },

  onMilestoneTap: function(e) {
    var id = e.currentTarget.dataset.id;
    var milestone = this.data.milestones.find(function(m) { return m.id === id; });
    if (milestone && milestone.action_card) {
      wx.navigateTo({
        url: '/pages/milestones/action-card?id=' + id
      });
    }
  },

  onAddCustom: function() {
    wx.navigateTo({ url: '/pages/milestones/add-custom' });
  }
});
