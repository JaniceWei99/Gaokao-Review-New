var app = getApp();
var storage = require('../../services/storage');
var districts = require('../../constants/districts');

Page({
  data: {
    districts: districts.DISTRICTS,
    selected: ''
  },

  onLoad: function() {
    var local = storage.getStudent() || {};
    if (local.district) {
      this.setData({ selected: local.district });
    }
  },

  onSelect: function(e) {
    var key = e.currentTarget.dataset.id;
    this.setData({ selected: key });

    var local = storage.getStudent() || {};
    local.district = key;
    local.district_name = districts.DISTRICTS.find(function(d) { return d.id === key; })?.name || '';
    storage.saveStudent(local);
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

    var isLoggedIn = app.isLoggedIn();
    var local = storage.getStudent() || {};

    if (!isLoggedIn) {
      local.name = local.name || '我的孩子';
      local._onboardingComplete = true;
      storage.saveStudent(local);

      app.globalData.currentStudent = local;
      wx.setStorageSync('currentStudent', local);
      wx.reLaunch({ url: '/pages/onboarding/complete' });
      return;
    }

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

      local._cloudId = student.id;
      storage.saveStudent(local);

      wx.navigateTo({ url: '/pages/onboarding/complete' });
    }).catch(function(err) {
      console.warn('[DistrictSelect] submit error:', err);
      local.name = local.name || '我的孩子';
      local._onboardingComplete = true;
      storage.saveStudent(local);

      app.globalData.currentStudent = local;
      wx.setStorageSync('currentStudent', local);
      wx.navigateTo({ url: '/pages/onboarding/complete' });
    });
  }
});
