var app = getApp();
var districts = require('../../constants/districts');

Page({
  data: {
    districts: districts.DISTRICTS,
    selected: ''
  },

  onSelect: function(e) {
    var key = e.currentTarget.dataset.id;
    this.setData({ selected: key });
  },

  onNext: function() {
    var onboarding = app.globalData.onboardingData || {};
    onboarding.district = this.data.selected || null;
    app.globalData.onboardingData = onboarding;

    this._submitOnboarding();
  },

  onSkip: function() {
    var onboarding = app.globalData.onboardingData || {};
    onboarding.district = null;
    app.globalData.onboardingData = onboarding;

    this._submitOnboarding();
  },

  _submitOnboarding: function() {
    var that = this;
    var onboarding = app.globalData.onboardingData || {};
    var api = require('../../services/api');

    var payload = {
      grade: onboarding.grade || 'gao1',
      has_selected_subjects: onboarding.has_selected_subjects || false,
      selected_subjects: onboarding.selected_subjects || null,
      has_jan_english_exam: onboarding.has_jan_english_exam || false,
      district: onboarding.district || null
    };

    api.post('/api/students', payload).then(function(res) {
      var student = res.student || res;
      app.globalData.currentStudent = student;
      wx.setStorageSync('currentStudent', student);

      wx.navigateTo({ url: '/pages/onboarding/complete' });
    }).catch(function(err) {
      console.warn('[DistrictSelect] submit error:', err);
      wx.showToast({ title: '提交失败，请重试', icon: 'none' });
    });
  }
});
