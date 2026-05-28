var api = require('../../services/api');
var app = getApp();

Page({
  data: {
    progressList: [],
    subjectId: '',
    subjectOptions: [
      { key: 'chinese', label: '语文' },
      { key: 'math', label: '数学' },
      { key: 'english', label: '英语' },
      { key: 'physics', label: '物理' },
      { key: 'chemistry', label: '化学' },
      { key: 'biology', label: '生物' },
      { key: 'politics', label: '政治' },
      { key: 'history', label: '历史' },
      { key: 'geography', label: '地理' }
    ],
    subjectIndex: -1,
    loading: true,
    showForm: false,
    formSubjectId: '',
    formSubjectIndex: -1,
    formContent: '',
    formStartDate: '',
    formEndDate: '',
    editingId: null
  },

  onLoad: function() {
    this.loadProgress();
  },

  onShow: function() {
    this.loadProgress();
  },

  loadProgress: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      that.setData({ loading: false });
      return;
    }

    var params = { student_id: studentId };
    if (that.data.subjectId) {
      params.subject_id = that.data.subjectId;
    }

    api.get('/api/students/' + studentId + '/school-progress', params).then(function(res) {
      that.setData({
        progressList: res || [],
        loading: false
      });
    }).catch(function() {
      that.setData({ loading: false });
    });
  },

  onSubjectFilter: function(e) {
    var idx = parseInt(e.detail.value);
    var subjectId = this.data.subjectOptions[idx].key;
    this.setData({ subjectIndex: idx, subjectId: subjectId });
    this.loadProgress();
  },

  onAdd: function() {
    this.setData({
      showForm: true,
      editingId: null,
      formSubjectId: '',
      formSubjectIndex: -1,
      formContent: '',
      formStartDate: '',
      formEndDate: ''
    });
  },

  onEdit: function(e) {
    var item = e.currentTarget.dataset.item;
    var subjectIdx = this.data.subjectOptions.findIndex(function(s) {
      return s.key === item.subject_id;
    });
    this.setData({
      showForm: true,
      editingId: item.id,
      formSubjectId: item.subject_id,
      formSubjectIndex: subjectIdx,
      formContent: item.content,
      formStartDate: item.start_date || '',
      formEndDate: item.end_date || ''
    });
  },

  onCancel: function() {
    this.setData({ showForm: false });
  },

  onFormSubjectChange: function(e) {
    var idx = parseInt(e.detail.value);
    this.setData({
      formSubjectIndex: idx,
      formSubjectId: this.data.subjectOptions[idx].key
    });
  },

  onContentInput: function(e) {
    this.setData({ formContent: e.detail.value });
  },

  onStartDateChange: function(e) {
    this.setData({ formStartDate: e.detail.value });
  },

  onEndDateChange: function(e) {
    this.setData({ formEndDate: e.detail.value });
  },

  onSubmit: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    if (!that.data.formSubjectId) {
      wx.showToast({ title: '请选择科目', icon: 'none' });
      return;
    }
    if (!that.data.formContent.trim()) {
      wx.showToast({ title: '请输入复习内容', icon: 'none' });
      return;
    }

    var payload = {
      subject_id: that.data.formSubjectId,
      content: that.data.formContent.trim(),
      start_date: that.data.formStartDate || null,
      end_date: that.data.formEndDate || null
    };

    if (that.data.editingId) {
      api.put('/api/students/' + studentId + '/school-progress/' + that.data.editingId, payload).then(function() {
        wx.showToast({ title: '已更新', icon: 'success' });
        that.setData({ showForm: false });
        that.loadProgress();
      }).catch(function() {
        wx.showToast({ title: '更新失败', icon: 'none' });
      });
    } else {
      api.post('/api/students/' + studentId + '/school-progress', payload).then(function() {
        wx.showToast({ title: '已添加', icon: 'success' });
        that.setData({ showForm: false });
        that.loadProgress();
      }).catch(function() {
        wx.showToast({ title: '添加失败', icon: 'none' });
      });
    }
  },

  onDelete: function(e) {
    var that = this;
    var id = e.currentTarget.dataset.id;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条复习进度吗？',
      success: function(res) {
        if (res.confirm) {
          api.del('/api/students/' + studentId + '/school-progress/' + id).then(function() {
            wx.showToast({ title: '已删除', icon: 'none' });
            that.loadProgress();
          }).catch(function() {
            wx.showToast({ title: '删除失败', icon: 'none' });
          });
        }
      }
    });
  },

  onViewErrors: function(e) {
    var id = e.currentTarget.dataset.id;
    var studentId = app.getCurrentStudentId();
    wx.navigateTo({
      url: '/pages/errors/list?student_id=' + studentId + '&progress_id=' + id
    });
  }
});
