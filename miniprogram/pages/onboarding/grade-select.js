var app = getApp();

Page({
  data: {
    grades: [
      { key: 'gao1', label: '高一', desc: '高中第一年' },
      { key: 'gao2', label: '高二', desc: '高中第二年' },
      { key: 'gao3', label: '高三', desc: '高考冲刺年' }
    ],
    selected: ''
  },

  onSelectGrade: function(e) {
    var grade = e.currentTarget.dataset.grade;
    this.setData({ selected: grade });
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
