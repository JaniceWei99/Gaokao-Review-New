var app = getApp();
var subjects = require('../../constants/subjects');

var ELECTIVES = subjects.ALL_SUBJECTS.filter(function(s) {
  return s.category === 'elective';
}).map(function(s) {
  return { key: s.id, label: s.name };
});

Page({
  data: {
    subjects: ELECTIVES,
    selected: [],
    grade: '',
    canSkip: true,
    maxSelect: 3
  },

  onLoad: function() {
    var onboarding = app.globalData.onboardingData || {};
    var grade = onboarding.grade || 'gao1';
    this.setData({
      grade: grade,
      canSkip: grade !== 'gao3'
    });
  },

  onToggleSubject: function(e) {
    var key = e.currentTarget.dataset.key;
    var selected = this.data.selected.slice();
    var idx = selected.indexOf(key);

    if (idx >= 0) {
      selected.splice(idx, 1);
    } else {
      if (selected.length >= this.data.maxSelect) {
        selected.shift();
      }
      selected.push(key);
    }

    this.setData({ selected: selected });
  },

  onNext: function() {
    var onboarding = app.globalData.onboardingData || {};
    var hasSelected = this.data.selected.length === 3;

    onboarding.has_selected_subjects = hasSelected;
    onboarding.selected_subjects = hasSelected ? this.data.selected : null;

    if (this.data.grade === 'gao3' && !hasSelected) {
      wx.showToast({ title: '高三必须选择3门选考科目', icon: 'none' });
      return;
    }

    app.globalData.onboardingData = onboarding;

    if (this.data.grade === 'gao3') {
      wx.navigateTo({ url: '/pages/onboarding/english-exam' });
    } else {
      wx.navigateTo({ url: '/pages/onboarding/district-select' });
    }
  },

  onSkip: function() {
    var onboarding = app.globalData.onboardingData || {};
    onboarding.has_selected_subjects = false;
    onboarding.selected_subjects = null;
    app.globalData.onboardingData = onboarding;
    wx.navigateTo({ url: '/pages/onboarding/district-select' });
  }
});
