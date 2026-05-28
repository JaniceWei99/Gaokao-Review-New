var app = getApp();
var errorNoteService = require('../../services/errorNote');
var api = require('../../services/api');
var permission = require('../../utils/permission');

Page({
  data: {
    note: null,
    loading: true,
    showDeleteConfirm: false,
    subscription: null,
    classifying: false,
    classification: null
  },

  onLoad: function(options) {
    this.studentId = options.studentId || app.getCurrentStudentId();
    this.noteId = options.id;
    this._loadNote();
    this._loadSubscription();
  },

  _loadSubscription: function() {
    var that = this;
    api.get('/api/subscription').then(function(res) {
      that.setData({ subscription: res });
    }).catch(function() {});
  },

  _loadNote: function() {
    var that = this;
    that.setData({ loading: true });

    errorNoteService.getErrorNote(that.studentId, that.noteId).then(function(res) {
      that.setData({ note: res, loading: false });
    }).catch(function(err) {
      console.warn('[ErrorDetail] load error:', err);
      that.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    });
  },

  onPreviewImage: function(e) {
    var that = this;
    var url = e.currentTarget.dataset.url;
    var urls = [];
    if (that.data.note.question_image_url) {
      urls.push(that.data.note.question_image_url);
    }
    if (that.data.note.correction_image_url) {
      urls.push(that.data.note.correction_image_url);
    }
    wx.previewImage({
      current: url,
      urls: urls
    });
  },

  onDelete: function() {
    this.setData({ showDeleteConfirm: true });
  },

  onCancelDelete: function() {
    this.setData({ showDeleteConfirm: false });
  },

  onConfirmDelete: function() {
    var that = this;
    that.setData({ showDeleteConfirm: false });

    errorNoteService.deleteErrorNote(that.studentId, that.noteId).then(function() {
      wx.showToast({ title: '已删除', icon: 'success' });
      setTimeout(function() {
        wx.navigateBack();
      }, 1000);
    }).catch(function(err) {
      console.warn('[ErrorDetail] delete error:', err);
      wx.showToast({ title: '删除失败', icon: 'none' });
    });
  },

  onClassifyWithAI: function() {
    var that = this;
    var sub = that.data.subscription;

    if (!sub || sub.plan !== 'premium') {
      permission.showUpgradeModal('FEATURE_REQUIRES_PREMIUM');
      return;
    }

    that.setData({ classifying: true });

    api.post('/api/students/' + that.studentId + '/ai/error-notes/' + that.noteId + '/classify').then(function(res) {
      that.setData({
        classification: res,
        classifying: false
      });
    }).catch(function(err) {
      console.warn('[ErrorDetail] classify error:', err);
      that.setData({ classifying: false });
      wx.showToast({ title: '分类失败', icon: 'none' });
    });
  }
});
