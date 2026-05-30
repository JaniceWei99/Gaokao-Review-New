var app = getApp();
var storage = require('../../services/storage');
var imageUtil = require('../../utils/image');
var uploadService = require('../../services/upload');
var errorNoteService = require('../../services/errorNote');
var subjects = require('../../constants/subjects');

var ERROR_TYPES = [
  { key: 'careless', label: '粗心' },
  { key: 'concept_unclear', label: '概念不清' },
  { key: 'method_unknown', label: '方法不会' },
  { key: 'other', label: '其他' }
];

var SOURCES = [
  { key: 'monthly', label: '月考' },
  { key: 'weekly', label: '周测' },
  { key: 'homework', label: '作业' },
  { key: 'mock', label: '模考' },
  { key: 'other', label: '其他' }
];

Page({
  data: {
    step: 1,
    questionImagePath: '',
    correctionImagePath: '',
    subjectList: [],
    selectedSubject: '',
    selectedKnowledgeNode: '',
    knowledgeNodes: [],
    errorTypes: ERROR_TYPES,
    sources: SOURCES,
    selectedErrorType: '',
    selectedSource: '',
    note: '',
    submitting: false
  },

  onLoad: function() {
    var student = app.globalData.currentStudent || storage.getStudent() || {};
    var grade = student.grade || 'gao1';
    var subjectList = subjects.ALL_SUBJECTS;

    if (grade !== 'gao1' && student.has_selected_subjects) {
      subjectList = subjectList.filter(function(s) {
        return s.category === 'required' ||
          (student.selected_subjects && student.selected_subjects.indexOf(s.id) >= 0);
      });
    }

    this.setData({ subjectList: subjectList });
  },

  onChooseQuestionImage: function() {
    var that = this;
    imageUtil.compressAndChoose(1).then(function(paths) {
      if (paths.length > 0) {
        that.setData({ questionImagePath: paths[0] });
      }
    });
  },

  onChooseCorrectionImage: function() {
    var that = this;
    imageUtil.compressAndChoose(1).then(function(paths) {
      if (paths.length > 0) {
        that.setData({ correctionImagePath: paths[0] });
      }
    });
  },

  onRemoveCorrection: function() {
    this.setData({ correctionImagePath: '' });
  },

  onNextToStep2: function() {
    if (!this.data.questionImagePath) {
      wx.showToast({ title: '请先拍摄题目照片', icon: 'none' });
      return;
    }
    this.setData({ step: 2 });
  },

  onSelectSubject: function(e) {
    var subjectId = e.currentTarget.dataset.id;
    this.setData({ selectedSubject: subjectId, selectedKnowledgeNode: '' });

    if (app.isLoggedIn()) {
      this._loadKnowledgeNodes(subjectId);
    }
  },

  _loadKnowledgeNodes: function(subjectId) {
    var that = this;
    var api = require('../../services/api');
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    api.get('/api/knowledge', { subject_id: subjectId, level: 2 }).then(function(res) {
      var nodes = res.nodes || res || [];
      that.setData({ knowledgeNodes: nodes });
    }).catch(function() {
      that.setData({ knowledgeNodes: [] });
    });
  },

  onSelectKnowledgeNode: function(e) {
    var nodeId = e.currentTarget.dataset.id;
    this.setData({ selectedKnowledgeNode: nodeId });
  },

  onNextToStep3: function() {
    if (!this.data.selectedSubject) {
      wx.showToast({ title: '请选择科目', icon: 'none' });
      return;
    }
    this.setData({ step: 3 });
  },

  onSelectErrorType: function(e) {
    var type = e.currentTarget.dataset.key;
    this.setData({ selectedErrorType: type });
  },

  onSelectSource: function(e) {
    var source = e.currentTarget.dataset.key;
    this.setData({ selectedSource: source });
  },

  onInputNote: function(e) {
    this.setData({ note: e.detail.value });
  },

  onGoBack: function() {
    var step = this.data.step;
    if (step > 1) {
      this.setData({ step: step - 1 });
    } else {
      wx.navigateBack();
    }
  },

  onSubmit: function() {
    var that = this;
    if (that.data.submitting) return;

    var isLoggedIn = app.isLoggedIn();
    var studentId = app.getCurrentStudentId();

    that.setData({ submitting: true });

    if (!isLoggedIn || !studentId) {
      var note = {
        id: 'local_' + Date.now(),
        subject_id: that.data.selectedSubject,
        knowledge_node_id: that.data.selectedKnowledgeNode || null,
        error_type: that.data.selectedErrorType || null,
        source: that.data.selectedSource || null,
        note: that.data.note || null,
        question_image_url: that.data.questionImagePath,
        correction_image_url: that.data.correctionImagePath || null,
        _localCreated: Date.now()
      };
      storage.saveErrorNote(note);
      wx.showToast({ title: '已保存到本地', icon: 'success' });
      setTimeout(function() { wx.navigateBack(); }, 1000);
      return;
    }

    that._uploadImages(studentId).then(function(urls) {
      var payload = {
        subject_id: that.data.selectedSubject,
        knowledge_node_id: that.data.selectedKnowledgeNode || null,
        error_type: that.data.selectedErrorType || null,
        source: that.data.selectedSource || null,
        note: that.data.note || null,
        question_image_url: urls.questionUrl,
        correction_image_url: urls.correctionUrl || null
      };

      return errorNoteService.createErrorNote(studentId, payload);
    }).then(function() {
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(function() { wx.navigateBack(); }, 1000);
    }).catch(function(err) {
      console.warn('[ErrorAdd] submit error:', err);
      that.setData({ submitting: false });
    });
  },

  _uploadImages: function(studentId) {
    var that = this;
    var questionPath = that.data.questionImagePath;
    var correctionPath = that.data.correctionImagePath;

    var questionPromise = that._uploadSingleImage(questionPath, 'errors', studentId);

    var correctionPromise = correctionPath
      ? that._uploadSingleImage(correctionPath, 'errors', studentId)
      : Promise.resolve(null);

    return Promise.all([questionPromise, correctionPromise]).then(function(results) {
      return {
        questionUrl: results[0],
        correctionUrl: results[1]
      };
    });
  },

  _uploadSingleImage: function(filePath, prefix, studentId) {
    return uploadService.requestUploadCredential(prefix, studentId).then(function(creds) {
      return uploadService.uploadImageToCOS(filePath, creds).then(function() {
        return creds.image_key;
      });
    });
  }
});