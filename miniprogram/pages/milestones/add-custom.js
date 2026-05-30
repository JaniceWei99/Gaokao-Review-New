var storage = require('../../services/storage');
var api = require('../../services/api');
var app = getApp();

Page({
  data: {
    name: '',
    event_date: '',
    description: '',
    submitting: false,
    isEdit: false,
    editId: ''
  },

  onLoad: function(options) {
    if (options.id) {
      var custom = wx.getStorageSync('local_custom_milestones') || [];
      var target = custom.find(function(m) { return m.id === options.id; });
      if (target) {
        this.setData({
          isEdit: true,
          editId: options.id,
          name: target.name || '',
          event_date: target.event_date || '',
          description: target.description || ''
        });
      }
    }
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

    that.setData({ submitting: true });

    if (d.isEdit) {
      that.doEdit();
    } else {
      that.doAdd();
    }
  },

  doAdd: function() {
    var that = this;
    var d = that.data;

    var milestone = {
      id: 'local_milestone_' + Date.now(),
      name: d.name.trim(),
      event_date: d.event_date,
      description: d.description.trim() || null,
      type: 'custom',
      _localCreated: Date.now()
    };

    var custom = wx.getStorageSync('local_custom_milestones') || [];
    custom.push(milestone);
    wx.setStorageSync('local_custom_milestones', custom);

    var isLoggedIn = app.isLoggedIn();
    var studentId = app.getCurrentStudentId();

    if (isLoggedIn && studentId) {
      api.post('/api/students/' + studentId + '/milestones', {
        title: d.name.trim(),
        event_date: d.event_date,
        description: d.description.trim() || null
      }).then(function() {
        that.setData({ submitting: false });
        wx.showToast({ title: '添加成功', icon: 'success' });
        setTimeout(function() { wx.navigateBack(); }, 1000);
      }).catch(function() {
        wx.showToast({ title: '已保存到本地', icon: 'success' });
        setTimeout(function() { wx.navigateBack(); }, 1000);
      });
    } else {
      wx.showToast({ title: '已保存到本地', icon: 'success' });
      setTimeout(function() { wx.navigateBack(); }, 1000);
    }
  },

  doEdit: function() {
    var that = this;
    var d = that.data;

    var custom = wx.getStorageSync('local_custom_milestones') || [];
    var idx = custom.findIndex(function(m) { return m.id === d.editId; });
    if (idx >= 0) {
      custom[idx].name = d.name.trim();
      custom[idx].event_date = d.event_date;
      custom[idx].description = d.description.trim() || null;
      custom[idx]._localUpdated = Date.now();
      wx.setStorageSync('local_custom_milestones', custom);
    }

    wx.showToast({ title: '已保存', icon: 'success' });
    setTimeout(function() { wx.navigateBack(); }, 1000);
  }
});
