var app = getApp();
var errorNoteService = require('../../services/errorNote');
var subjects = require('../../constants/subjects');
var dateUtil = require('../../utils/date');

var ERROR_TYPE_MAP = {
  careless: '粗心',
  concept_unclear: '概念不清',
  method_unknown: '方法不会',
  other: '其他'
};

var SOURCE_MAP = {
  monthly: '月考',
  weekly: '周测',
  homework: '作业',
  mock: '模考',
  other: '其他'
};

Page({
  data: {
    subjects: subjects.ALL_SUBJECTS,
    currentSubject: '',
    errorNotes: [],
    stats: null,
    loading: false,
    page: 1,
    hasMore: true
  },

  onLoad: function() {
    this._loadErrorNotes();
    this._loadStats();
  },

  onShow: function() {
    if (this._needRefresh) {
      this._needRefresh = false;
      this.setData({ page: 1, errorNotes: [], hasMore: true });
      this._loadErrorNotes();
      this._loadStats();
    }
  },

  onHide: function() {
    this._needRefresh = true;
  },

  onFilterSubject: function(e) {
    var subject = e.currentTarget.dataset.subject;
    this.setData({
      currentSubject: subject,
      page: 1,
      errorNotes: [],
      hasMore: true
    });
    this._loadErrorNotes();
  },

  _loadErrorNotes: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    that.setData({ loading: true });

    var params = {
      page: that.data.page,
      page_size: 20,
      sort: 'newest'
    };

    if (that.data.currentSubject) {
      params.subject_id = that.data.currentSubject;
    }

    errorNoteService.listErrorNotes(studentId, params).then(function(res) {
      var notes = (res.error_notes || []).map(function(item) {
        return {
          id: item.id,
          subject_id: item.subject_id,
          error_type: item.error_type,
          error_type_label: ERROR_TYPE_MAP[item.error_type] || item.error_type || '',
          source: item.source,
          source_label: SOURCE_MAP[item.source] || item.source || '',
          question_image_url: item.question_image_url,
          note: item.note,
          created_at: item.created_at,
          created_at_display: item.created_at ? dateUtil.formatDate(item.created_at) : ''
        };
      });

      that.setData({
        errorNotes: that.data.page === 1 ? notes : that.data.errorNotes.concat(notes),
        hasMore: notes.length >= 20,
        loading: false
      });
    }).catch(function(err) {
      console.warn('[ErrorList] load error:', err);
      that.setData({ loading: false });
    });
  },

  _loadStats: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    errorNoteService.getErrorNoteStats(studentId).then(function(stats) {
      that.setData({ stats: stats });
    }).catch(function() {});
  },

  onReachBottom: function() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 });
      this._loadErrorNotes();
    }
  },

  onGoToAdd: function() {
    wx.navigateTo({ url: '/pages/errors/add' });
  }
});
