var app = getApp();

Page({
  data: {
    selected: ''
  },

  onSelect: function(e) {
    var value = e.currentTarget.dataset.value;
    this.setData({ selected: value });
  },

  onNext: function() {
    if (!this.data.selected) {
      wx.showToast({ title: '请选择是否报名1月外语考试', icon: 'none' });
      return;
    }

    var onboarding = app.globalData.onboardingData || {};
    onboarding.has_jan_english_exam = (this.data.selected === 'yes');
    app.globalData.onboardingData = onboarding;

    wx.navigateTo({ url: '/pages/onboarding/district-select' });
  }
});
