var api = require('../../services/api');
var dateUtil = require('../../utils/date');
var app = getApp();

Page({
  data: {
    milestone: null,
    loading: true
  },

  onLoad: function(options) {
    if (options.id) {
      this.loadMilestone(options.id);
    }
  },

  loadMilestone: function(id) {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      that.setData({ loading: false });
      return;
    }

    api.get('/api/students/' + studentId + '/milestones').then(function(res) {
      var list = res.milestones || res.data || res || [];
      var milestone = list.find(function(m) { return m.id === id; });
      if (milestone) {
        milestone.date_display = dateUtil.formatDate(milestone.event_date);
        milestone.relative = dateUtil.formatRelative(milestone.event_date);
      }
      that.setData({
        milestone: milestone || null,
        loading: false
      });
    }).catch(function() {
      that.setData({ loading: false });
    });
  }
});
