var app = getApp();
var storage = require('../../services/storage');
var regions = require('../../constants/regions');

Page({
  data: {
    districts: regions.getRegions('shanghai'),
    selected: ''
  },

  onLoad: function() {
    var local = storage.getStudent() || {};
    if (local.region_code || local.district) {
      this.setData({ selected: local.region_code || local.district });
    }
  },

  onSelect: function(e) {
    var key = e.currentTarget.dataset.id;
    this.setData({ selected: key });

    var local = storage.getStudent() || {};
    local.region_code = key;
    local.district_name = regions.ALL_REGIONS.find(function(d) { return d.id === key; })?.name || '';
    storage.saveStudent(local);
  },

  onNext: function() {
    var onboarding = app.globalData.onboardingData || {};
    onboarding.region_code = this.data.selected || null;
    app.globalData.onboardingData = onboarding;

    this._submitOnboarding();
  },

  onSkip: function() {
    var onboarding = app.globalData.onboardingData || {};
    onboarding.region_code = null;
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
      region_code: onboarding.region_code || null
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
