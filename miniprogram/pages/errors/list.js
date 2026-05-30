var app = getApp();
var storage = require('../../services/storage');
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

var SUBJECT_NAME_MAP = {};
subjects.ALL_SUBJECTS.forEach(function(s) {
  SUBJECT_NAME_MAP[s.id] = s.name;
});

Page({
  data: {
    subjects: subjects.ALL_SUBJECTS,
    currentSubject: '',
    errorNotes: [],
    stats: null,
    loading: false,
    source: 'local',
    isLoggedIn: false
  },

  onLoad: function() {
    this.setData({ isLoggedIn: app.isLoggedIn() });
    this._loadErrorNotes();
  },

  onShow: function() {
    var loggedIn = app.isLoggedIn();
    if (this._needRefresh || this.data.isLoggedIn !== loggedIn) {
      this._needRefresh = false;
      this.setData({ isLoggedIn: loggedIn });
      this._loadErrorNotes();
    }
  },

  onHide: function() {
    this._needRefresh = true;
  },

  onFilterSubject: function(e) {
    var subject = e.currentTarget.dataset.subject;
    this.setData({
      currentSubject: subject,
      errorNotes: []
    });
    this._loadErrorNotes();
  },

  _loadErrorNotes: function() {
    var local = storage.getErrorNotes();
    var filteredLocal = local;
    if (this.data.currentSubject) {
      filteredLocal = local.filter(function(n) {
        return n.subject_id === this.data.currentSubject;
      }.bind(this));
    }

    if (filteredLocal.length > 0) {
      this.setData({
        errorNotes: this._processNotes(filteredLocal),
        loading: false,
        source: 'local'
      });
    }

    if (app.isLoggedIn()) {
      this._loadFromCloud();
    } else if (local.length === 0) {
      this.setData({ loading: false });
    }
  },

  _loadFromCloud: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    that.setData({ loading: true });

    var params = {
      page: 1,
      page_size: 100,
      sort: 'newest'
    };

    if (that.data.currentSubject) {
      params.subject_id = that.data.currentSubject;
    }

    errorNoteService.listErrorNotes(studentId, params).then(function(res) {
      var cloud = (res.error_notes || []);
      cloud.forEach(function(n) {
        storage.saveErrorNote({
          id: n.id,
          subject_id: n.subject_id,
          knowledge_node_id: n.knowledge_node_id,
          error_type: n.error_type,
          source: n.source,
          note: n.note,
          question_image_url: n.question_image_url,
          correction_image_url: n.correction_image_url,
          created_at: n.created_at
        });
      });

      var merged = storage.getErrorNotes();
      var filteredMerged = merged;
      if (that.data.currentSubject) {
        filteredMerged = merged.filter(function(n) {
          return n.subject_id === that.data.currentSubject;
        });
      }

      that.setData({
        errorNotes: that._processNotes(filteredMerged),
        loading: false,
        source: cloud.length > 0 ? 'cloud' : 'local'
      });
    }).catch(function(err) {
      console.warn('[ErrorList] cloud load error:', err);
      that.setData({ loading: false });
    });
  },

  _processNotes: function(notes) {
    return notes.map(function(item) {
      return {
        id: item.id,
        subject_id: item.subject_id,
        subject_name: SUBJECT_NAME_MAP[item.subject_id] || item.subject_id,
        error_type: item.error_type,
        error_type_label: ERROR_TYPE_MAP[item.error_type] || item.error_type || '',
        source: item.source,
        source_label: SOURCE_MAP[item.source] || item.source || '',
        knowledge_node_id: item.knowledge_node_id,
        question_image_url: item.question_image_url,
        correction_image_url: item.correction_image_url,
        note: item.note,
        created_at: item.created_at || item._localCreated,
        created_at_display: item.created_at ? dateUtil.formatDate(item.created_at) : ''
      };
    });
  },

  onGoToAdd: function() {
    wx.navigateTo({ url: '/pages/errors/add' });
  }
});