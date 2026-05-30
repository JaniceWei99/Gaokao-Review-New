var auth = require('../../services/auth');
var app = getApp();

Page({
  data: {
    loading: false,
    hasNavigated: false
  },

  onLoad: function() {
    var that = this;
    if (app.isLoggedIn()) {
      auth.checkOnboarding().then(function(needsOnboarding) {
        if (!needsOnboarding && !that.data.hasNavigated) {
          that.setData({ hasNavigated: true });
          wx.switchTab({ 
            url: '/pages/index/index',
            fail: function(err) {
              console.error('switchTab failed:', err);
              that.setData({ hasNavigated: false });
            }
          });
        }
      }).catch(function(err) {
        console.error('checkOnboarding failed:', err);
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
