var api = require('../../services/api');
var storage = require('../../services/storage');
var dateUtil = require('../../utils/date');
var localMilestones = require('../../constants/milestones');
var app = getApp();

Page({
  data: {
    milestones: [],
    loading: true,
    showPast: false,
    isLoggedIn: false,
    source: 'local'
  },

  onLoad: function() {
    this.setData({ isLoggedIn: app.isLoggedIn() });
    this.loadMilestones();
  },

  onShow: function() {
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

    if (!app.isLoggedIn() || !studentId) {
      var student = storage.getStudent() || app.globalData.currentStudent;
      var grade = student ? student.grade : 'gao3';
      console.log('[Timeline] local mode - student:', student, 'grade:', grade);
      var systemList = localMilestones.getMilestones(grade);
      var customMilestones = wx.getStorageSync('local_custom_milestones') || [];

      var allList = [];

      systemList.forEach(function(m) {
        var days = dateUtil.daysUntil(m.event_date);
        var isPast = days < 0;
        if (grade === 'gao3' && isPast) return;
        allList.push({
          id: m.id,
          name: m.name,
          event_date: m.event_date,
          date_display: dateUtil.formatDate(m.event_date),
          relative: dateUtil.formatRelative(m.event_date),
          days_away: days,
          is_past: isPast,
          is_today: days === 0,
          type: 'system',
          action_card: null
        });
      });

      customMilestones.forEach(function(m) {
        var days = dateUtil.daysUntil(m.event_date);
        allList.push({
          id: m.id,
          name: m.name,
          event_date: m.event_date,
          description: m.description || '',
          date_display: dateUtil.formatDate(m.event_date),
          relative: dateUtil.formatRelative(m.event_date),
          days_away: days,
          is_past: days < 0,
          is_today: days === 0,
          type: 'custom',
          action_card: null
        });
      });

      allList.sort(function(a, b) {
        return a.days_away - b.days_away;
      });

      this.setData({
        milestones: allList,
        loading: false,
        source: 'local'
      });
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

      var custom = wx.getStorageSync('local_custom_milestones') || [];
      custom.forEach(function(m) {
        var days = dateUtil.daysUntil(m.event_date);
        list.push({
          id: m.id,
          name: m.name,
          event_date: m.event_date,
          date_display: dateUtil.formatDate(m.event_date),
          relative: dateUtil.formatRelative(m.event_date),
          days_away: days,
          is_past: days < 0,
          is_today: days === 0,
          type: 'custom',
          action_card: null
        });
      });

      list.sort(function(a, b) {
        return Math.abs(a.days_away) - Math.abs(b.days_away);
      });

      that.setData({
        milestones: list,
        loading: false,
        source: 'cloud'
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

  onDeleteMilestone: function(e) {
    var that = this;
    var milestoneId = e.currentTarget.dataset.id;

    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个里程碑吗？',
      success: function(res) {
        if (res.confirm) {
          var custom = wx.getStorageSync('local_custom_milestones') || [];
          custom = custom.filter(function(m) { return m.id !== milestoneId; });
          wx.setStorageSync('local_custom_milestones', custom);
          wx.showToast({ title: '已删除', icon: 'success' });
          that.loadMilestones();
        }
      }
    });
  },

  onEditMilestone: function(e) {
    var milestoneId = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/milestones/add-custom?id=' + milestoneId });
  },

  onAddCustom: function() {
    wx.navigateTo({ url: '/pages/milestones/add-custom' });
  }
});