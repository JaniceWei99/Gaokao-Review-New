// pages/profile/index.js — Profile Page
const auth = require('../../services/auth');
const { PLANS } = require('../../constants/plans');

const app = getApp();

Page({
  data: {
    isLoggedIn: false,
    userInfo: {},
    currentStudent: null,
    planName: '免费版',
    subscription: null
  },

  onLoad() {
    this.refreshData();
  },

  onShow() {
    this.refreshData();
  },

  /**
   * Refresh profile data.
   */
  refreshData() {
    const isLoggedIn = app.isLoggedIn();
    const userInfo = app.globalData.userInfo || {};
    const currentStudent = app.globalData.currentStudent;

    // Determine plan name
    let planName = '免费版';
    if (userInfo.plan && PLANS[userInfo.plan]) {
      planName = PLANS[userInfo.plan].name;
    }

    this.setData({
      isLoggedIn: isLoggedIn,
      userInfo: userInfo,
      currentStudent: currentStudent,
      planName: planName,
      subscription: userInfo.subscription || null
    });
  },

  /**
   * Login via WeChat.
   */
  async onLogin() {
    if (this.data.isLoggedIn) return;

    try {
      wx.showLoading({ title: '登录中...' });
      const result = await auth.wxLogin();
      wx.hideLoading();

      if (result.is_new_user) {
        wx.navigateTo({ url: '/pages/onboarding/welcome' });
      } else {
        this.refreshData();
      }
    } catch (err) {
      wx.hideLoading();
      console.warn('[Profile] login error:', err);
    }
  },

  /**
   * Logout.
   */
  onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '退出登录后本地数据将被清除',
      confirmText: '确认退出',
      cancelText: '取消',
      success(res) {
        if (res.confirm) {
          auth.logout();
        }
      }
    });
  },

  onNavigateTo(e) {
    var url = e.currentTarget.dataset.url;
    if (url) {
      wx.navigateTo({ url: url });
    }
  },

  onUpgradeToPremium() {
    wx.navigateTo({ url: '/pages/profile/subscription' });
  }
});
