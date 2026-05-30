// pages/profile/index.js — Profile Page
const auth = require('../../services/auth');
const storage = require('../../services/storage');
const sync = require('../../services/sync');
const { PLANS } = require('../../constants/plans');

const app = getApp();

Page({
  data: {
    isLoggedIn: false,
    userInfo: {},
    currentStudent: null,
    planName: '免费版',
    subscription: null,
    localSummary: {},
    hasLocalData: false,
    localDataCount: 0
  },

  onLoad() {
    this.refreshData();
  },

  onShow() {
    this.refreshData();
  },

  refreshData() {
    const isLoggedIn = app.isLoggedIn();
    const userInfo = app.globalData.userInfo || {};
    const currentStudent = app.globalData.currentStudent || storage.getStudent();

    let planName = '免费版';
    if (userInfo.plan && PLANS[userInfo.plan]) {
      planName = PLANS[userInfo.plan].name;
    }

    const localSummary = storage.getLocalDataSummary();
    const localDataCount = (localSummary.examsCount || 0) +
      (localSummary.errorNotesCount || 0) +
      (localSummary.growthRecordsCount || 0);
    const hasLocalData = localDataCount > 0;

    this.setData({
      isLoggedIn: isLoggedIn,
      userInfo: userInfo,
      currentStudent: currentStudent,
      planName: planName,
      subscription: userInfo.subscription || null,
      localSummary: localSummary,
      hasLocalData: hasLocalData,
      localDataCount: localDataCount
    });
  },

  async onLogin() {
    if (this.data.isLoggedIn) return;

    try {
      wx.showLoading({ title: '登录中...' });
      const result = await auth.wxLogin();
      wx.hideLoading();

      if (result.is_new_user) {
        const localSummary = storage.getLocalDataSummary();
        if (localSummary.examsCount > 0 || localSummary.errorNotesCount > 0 || localSummary.growthRecordsCount > 0) {
          wx.showModal({
            title: '检测到本地数据',
            content: `您有 ${localSummary.examsCount + localSummary.errorNotesCount + localSummary.growthRecordsCount} 条本地数据，是否同步到云端？`,
            confirmText: '同步',
            cancelText: '暂不',
            success: (res) => {
              if (res.confirm) {
                this.doSync();
              }
              wx.navigateTo({ url: '/pages/onboarding/grade-select' });
            }
          });
        } else {
          wx.navigateTo({ url: '/pages/onboarding/grade-select' });
        }
      } else {
        this.refreshData();
        const syncResult = await sync.syncAll();
        if (syncResult.success) {
          wx.showToast({ title: '数据已同步', icon: 'success' });
        }
      }
    } catch (err) {
      wx.hideLoading();
      console.warn('[Profile] login error:', err);
      wx.showToast({ title: '登录失败，请重试', icon: 'none' });
    }
  },

  async doSync() {
    wx.showLoading({ title: '同步中...' });
    const result = await sync.syncAll();
    wx.hideLoading();
    if (result.success) {
      wx.showToast({ title: `已同步 ${result.stats.exams + result.stats.errorNotes + result.stats.growthRecords} 条数据`, icon: 'success' });
      this.refreshData();
    } else {
      wx.showToast({ title: '同步失败，请检查网络', icon: 'none' });
    }
  },

  onLogout() {
    wx.showModal({
      title: '确认退出',
      content: '退出后本地数据仍保留，可随时重新登录同步',
      confirmText: '确认退出',
      cancelText: '取消',
      success(res) {
        if (res.confirm) {
          const userInfo = app.globalData.userInfo;
          app.globalData.token = null;
          app.globalData.userInfo = null;
          app.globalData.currentStudent = null;
          wx.removeStorageSync('token');
          wx.removeStorageSync('userInfo');
          wx.removeStorageSync('currentStudent');
          wx.reLaunch({ url: '/pages/index/index' });
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
