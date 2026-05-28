var api = require('../../services/api');
var app = getApp();

Page({
  data: {
    name: '',
    event_date: '',
    description: '',
    submitting: false
  },

  onNameInput: function(e) {
    this.setData({ name: e.detail.value });
  },

  onDateChange: function(e) {
    this.setData({ event_date: e.detail.value });
  },

  onDescInput: function(e) {
    this.setData({ description: e.detail.value });
  },

  onSubmit: function() {
    var that = this;
    var d = that.data;

    if (!d.name.trim()) {
      wx.showToast({ title: '请输入里程碑名称', icon: 'none' });
      return;
    }
    if (!d.event_date) {
      wx.showToast({ title: '请选择日期', icon: 'none' });
      return;
    }

    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    that.setData({ submitting: true });

    api.post('/api/students/' + studentId + '/milestones', {
      name: d.name.trim(),
      event_date: d.event_date,
      description: d.description.trim() || null,
      type: 'custom'
    }).then(function() {
      that.setData({ submitting: false });
      wx.showToast({ title: '添加成功', icon: 'success' });
      setTimeout(function() {
        wx.navigateBack();
      }, 1000);
    }).catch(function(err) {
      that.setData({ submitting: false });
      wx.showToast({ title: err.message || '添加失败', icon: 'none' });
    });
  }
});
