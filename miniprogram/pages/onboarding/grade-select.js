var app = getApp();
var storage = require('../../services/storage');

Page({
  data: {
    grades: [
      { key: 'gao1', label: '高一', desc: '高中第一年' },
      { key: 'gao2', label: '高二', desc: '高中第二年' },
      { key: 'gao3', label: '高三', desc: '高考冲刺年' }
    ],
    selected: ''
  },

  onLoad: function() {
    var local = storage.getStudent();
    if (local && local.grade) {
      this.setData({ selected: local.grade });
    }
  },

  onSelectGrade: function(e) {
    var grade = e.currentTarget.dataset.grade;
    this.setData({ selected: grade });

    var local = storage.getStudent() || {};
    local.grade = grade;
    local.grade_display = this.data.grades.find(function(g) { return g.key === grade; }).label;
    storage.saveStudent(local);

    app.globalData.onboardingData = app.globalData.onboardingData || {};
    app.globalData.onboardingData.grade = grade;
  },

  onNext: function() {
    if (!this.data.selected) {
      wx.showToast({ title: '请选择年级', icon: 'none' });
      return;
    }
    wx.navigateTo({ url: '/pages/onboarding/subject-select' });
  }
});
