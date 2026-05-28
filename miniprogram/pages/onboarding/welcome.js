var auth = require('../../services/auth');
var app = getApp();

Page({
  data: {
    loading: false
  },

  onLoad: function() {
    if (app.isLoggedIn()) {
      auth.checkOnboarding().then(function(needsOnboarding) {
        if (!needsOnboarding) {
          wx.switchTab({ url: '/pages/index/index' });
        }
      });
    }
  },

  onStartTap: function() {
    var that = this;
    that.setData({ loading: true });

    if (!app.isLoggedIn()) {
      auth.wxLogin().then(function() {
        that.setData({ loading: false });
        wx.navigateTo({ url: '/pages/onboarding/grade-select' });
      }).catch(function() {
        that.setData({ loading: false });
        wx.showToast({ title: '登录失败，请重试', icon: 'none' });
      });
    } else {
      that.setData({ loading: false });
      wx.navigateTo({ url: '/pages/onboarding/grade-select' });
    }
  }
});
