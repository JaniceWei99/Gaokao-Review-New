var api = require('../../services/api');
var storage = require('../../services/storage');
var dateUtil = require('../../utils/date');
var app = getApp();

var SUBJECTS = [
  { key: 'chinese', label: '语文', default_max: 150 },
  { key: 'math', label: '数学', default_max: 150 },
  { key: 'english', label: '英语', default_max: 150 },
  { key: 'physics', label: '物理', default_max: 100 },
  { key: 'chemistry', label: '化学', default_max: 100 },
  { key: 'biology', label: '生物', default_max: 100 },
  { key: 'politics', label: '政治', default_max: 100 },
  { key: 'history', label: '历史', default_max: 100 },
  { key: 'geography', label: '地理', default_max: 100 }
];

Page({
  data: {
    name: '',
    exam_type: 'monthly',
    exam_date: '',
    typeOptions: [
      { key: 'monthly', label: '月考' },
      { key: 'midterm', label: '期中' },
      { key: 'final', label: '期末' },
      { key: 'mock', label: '模考' },
      { key: 'other', label: '其他' }
    ],
    typeIndex: 0,
    subjects: SUBJECTS,
    activeSubjects: [],
    scores: {},
    submitting: false,
    progressDetected: null
  },

  onLoad: function() {
    var today = dateUtil.toDateString();
    this.setData({ exam_date: today });
    this.loadLastMaxScores();
  },

  loadLastMaxScores: function() {
    var that = this;

    if (app.isLoggedIn()) {
      var studentId = app.getCurrentStudentId();
      if (studentId) {
        api.get('/api/students/' + studentId + '/exams/last-max-scores', {}, { showError: false }).then(function(res) {
          var lastMax = res.last_max_scores || {};
          var scores = {};
          SUBJECTS.forEach(function(s) {
            if (lastMax[s.key]) {
              scores[s.key] = { max_score: lastMax[s.key], score: '' };
            }
          });
          that.setData({ scores: scores });
        }).catch(function() {});
      }
    }
  },

  onNameInput: function(e) {
    this.setData({ name: e.detail.value });
  },

  onDateChange: function(e) {
    this.setData({ exam_date: e.detail.value });
  },

  onTypeChange: function(e) {
    var idx = parseInt(e.detail.value);
    this.setData({
      typeIndex: idx,
      exam_type: this.data.typeOptions[idx].key
    });
  },

  onToggleSubject: function(e) {
    var key = e.currentTarget.dataset.key;
    var active = this.data.activeSubjects.slice();
    var scores = JSON.parse(JSON.stringify(this.data.scores));
    var idx = active.indexOf(key);

    if (idx >= 0) {
      active.splice(idx, 1);
      delete scores[key];
    } else {
      active.push(key);
      var subj = SUBJECTS.find(function(s) { return s.key === key; });
      if (!scores[key]) {
        scores[key] = { score: '', max_score: subj.default_max };
      }
    }

    this.setData({ activeSubjects: active, scores: scores });
  },

  onScoreInput: function(e) {
    var key = e.currentTarget.dataset.key;
    var val = e.detail.value;
    var scores = JSON.parse(JSON.stringify(this.data.scores));
    scores[key].score = val;
    this.setData({ scores: scores });
  },

  onMaxScoreInput: function(e) {
    var key = e.currentTarget.dataset.key;
    var val = e.detail.value;
    var scores = JSON.parse(JSON.stringify(this.data.scores));
    scores[key].max_score = parseFloat(val) || 0;
    this.setData({ scores: scores });
  },

  onSubmit: function() {
    var that = this;
    var d = that.data;

    if (!d.name.trim()) {
      wx.showToast({ title: '请输入考试名称', icon: 'none' });
      return;
    }
    if (!d.exam_date) {
      wx.showToast({ title: '请选择考试日期', icon: 'none' });
      return;
    }
    if (d.activeSubjects.length === 0) {
      wx.showToast({ title: '请至少选择一门科目', icon: 'none' });
      return;
    }

    var scoreList = [];
    var hasEmpty = false;
    d.activeSubjects.forEach(function(key) {
      var s = d.scores[key];
      if (!s || !s.score) {
        hasEmpty = true;
        return;
      }
      scoreList.push({
        subject_id: key,
        subject_name: SUBJECTS.find(function(s2) { return s2.key === key; }).label,
        score: parseFloat(s.score),
        max_score: s.max_score || 150
      });
    });

    if (hasEmpty) {
      wx.showToast({ title: '请填写所有科目的成绩', icon: 'none' });
      return;
    }

    that.setData({ submitting: true });

    var isLoggedIn = app.isLoggedIn();
    var studentId = app.getCurrentStudentId();

    if (!isLoggedIn || !studentId) {
      var examData = {
        id: 'local_' + Date.now(),
        name: d.name.trim(),
        exam_type: d.exam_type,
        exam_date: d.exam_date,
        scores: scoreList,
        _localCreated: Date.now()
      };
      storage.saveExam(examData);

      wx.showToast({ title: '已保存到本地', icon: 'success' });
      setTimeout(function() {
        wx.navigateBack();
      }, 1000);
      return;
    }

    api.post('/api/students/' + studentId + '/exams', {
      name: d.name.trim(),
      exam_type: d.exam_type,
      exam_date: d.exam_date,
      scores: scoreList
    }).then(function(res) {
      that.setData({ submitting: false });

      if (res.progress_detected && res.progress_detected.length > 0) {
        that.setData({ progressDetected: res.progress_detected });
        that.showProgressModal(res.progress_detected);
      } else {
        wx.showToast({ title: '录入成功', icon: 'success' });
        setTimeout(function() {
          wx.navigateBack();
        }, 1000);
      }
    }).catch(function(err) {
      that.setData({ submitting: false });
      wx.showToast({ title: err.message || '录入失败', icon: 'none' });
    });
  },

  showProgressModal: function(progress) {
    var that = this;

    var subjectList = progress.map(function(p) {
      return p.subject_name + '进步' + p.improvement + '%';
    }).join('、');

    var content = '🎉 ' + subjectList + '！要记录到成长册吗？';

    var firstProgress = progress[0];
    var recordTitle = progress.length === 1
      ? firstProgress.subject_name + '进步' + firstProgress.improvement + '%'
      : progress.length + '科进步';

    wx.showModal({
      title: '进步啦！',
      content: content,
      cancelText: '下次再说',
      confirmText: '记录进步🏆',
      success: function(res) {
        if (res.confirm) {
          var description = progress.map(function(p) {
            return p.subject_name + '：得分率从' + p.previous_rate + '%提升到' + p.current_rate + '%（提升' + p.improvement + '个百分点）';
          }).join('\n');

          var params = '?record_type=' + encodeURIComponent('progress') +
            '&title=' + encodeURIComponent(recordTitle) +
            '&description=' + encodeURIComponent(description) +
            '&auto_generated=1';

          wx.redirectTo({
            url: '/pages/growth/add' + params
          });
        } else {
          wx.navigateBack();
        }
      }
    });
  }
});