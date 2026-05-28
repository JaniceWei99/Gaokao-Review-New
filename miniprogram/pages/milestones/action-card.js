var api = require('../../services/api');
var permission = require('../../utils/permission');
var dateUtil = require('../../utils/date');
var app = getApp();

Page({
  data: {
    milestoneId: '',
    studentId: '',
    actionCard: null,
    checkedIndexes: [],
    progress: 0,
    timing: '',
    milestone: null,
    loading: true,
    toggling: false
  },

  onLoad: function(options) {
    this.setData({
      milestoneId: options.id || '',
      timing: options.timing || ''
    });
  },

  onShow: function() {
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      this.setData({ loading: false });
      return;
    }
    this.setData({ studentId: studentId });
    this.loadActionCard();
  },

  loadActionCard: function() {
    var that = this;
    var milestoneId = that.data.milestoneId;
    var studentId = that.data.studentId;

    api.get('/api/students/' + studentId + '/action-cards/milestones/' + milestoneId + '/action-card').then(function(res) {
      var card = res.action_card;
      var checked = res.checked_indexes || [];
      var progress = res.progress || 0;
      var timing = res.timing || '';

      if (card && card.action_items) {
        card.action_items = card.action_items.map(function(item, idx) {
          item.checked = checked.indexOf(idx) >= 0;
          return item;
        });
      }

      that.setData({
        actionCard: card,
        checkedIndexes: checked,
        progress: progress,
        timing: timing,
        loading: false
      });

      that.loadMilestoneInfo();
    }).catch(function(err) {
      console.error('Failed to load action card:', err);
      that.setData({ loading: false });
    });
  },

  loadMilestoneInfo: function() {
    var that = this;
    var milestoneId = that.data.milestoneId;
    var studentId = that.data.studentId;

    api.get('/api/students/' + studentId + '/milestones').then(function(res) {
      var list = res.milestones || [];
      var milestone = list.find(function(m) { return m.id === milestoneId; });
      if (milestone) {
        milestone.date_display = dateUtil.formatDate(milestone.event_date);
        milestone.relative = dateUtil.formatRelative(milestone.event_date);
        that.setData({ milestone: milestone });
      }
    }).catch(function() {});
  },

  onToggleItem: function(e) {
    var that = this;
    var index = e.currentTarget.dataset.index;
    var actionCard = that.data.actionCard;
    var studentId = that.data.studentId;

    if (that.data.toggling) return;
    that.setData({ toggling: true });

    api.post('/api/students/' + studentId + '/action-cards/cards/' + actionCard.id + '/toggle', {
      item_index: index
    }).then(function(res) {
      var checked = res.checked_indexes || [];
      var progress = res.progress || 0;

      actionCard.action_items = actionCard.action_items.map(function(item, idx) {
        item.checked = checked.indexOf(idx) >= 0;
        return item;
      });

      that.setData({
        actionCard: actionCard,
        checkedIndexes: checked,
        progress: progress,
        toggling: false
      });

      if (progress >= 1) {
        wx.showToast({ title: '全部完成！太棒了！', icon: 'success' });
      }
    }).catch(function() {
      that.setData({ toggling: false });
      wx.showToast({ title: '操作失败', icon: 'none' });
    });
  },

  onShareAppMessage: function() {
    var milestone = this.data.milestone;
    return {
      title: milestone ? milestone.title + ' - 行动清单' : '高考复习行动清单',
      path: '/pages/milestones/action-card?id=' + this.data.milestoneId
    };
  }
});
