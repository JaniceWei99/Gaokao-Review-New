var auth = require('../../services/auth');
var storage = require('../../services/storage');
var sync = require('../../services/sync');
var { PLANS } = require('../../constants/plans');
var account = require('../../services/account');

var app = getApp();

Page({
  data: {
    isLoggedIn: false,
    userInfo: {},
    currentAccountName: '',
    currentStudent: null,
    planName: '免费版',
    subscription: null,
    localSummary: {},
    hasLocalData: false,
    localDataCount: 0
  },

  onLoad: function() {
    this.refreshData();
  },

  onShow: function() {
    this.refreshData();
  },

  refreshData: function() {
    var isLoggedIn = app.isLoggedIn();
    var userInfo = app.globalData.userInfo || {};
    var currentStudent = app.globalData.currentStudent || storage.getStudent();
    var currentAccount = account.getCurrentAccount();

    var planName = '免费版';
    if (userInfo.plan && PLANS[userInfo.plan]) {
      planName = PLANS[userInfo.plan].name;
    }

    var localSummary = storage.getLocalDataSummary();
    var localDataCount = (localSummary.examsCount || 0) +
      (localSummary.errorNotesCount || 0) +
      (localSummary.growthRecordsCount || 0);
    var hasLocalData = localDataCount > 0;

    this.setData({
      isLoggedIn: isLoggedIn,
      userInfo: userInfo,
      currentAccountName: currentAccount ? currentAccount.name : '',
      currentStudent: currentStudent,
      planName: planName,
      subscription: userInfo.subscription || null,
      localSummary: localSummary,
      hasLocalData: hasLocalData,
      localDataCount: localDataCount
    });
  },

  onLogin: function() {
    if (this.data.isLoggedIn) return;

    var that = this;
    wx.showLoading({ title: '登录中...' });
    auth.wxLogin().then(function(result) {
      wx.hideLoading();

      if (result.is_new_user) {
        var localSummary = storage.getLocalDataSummary();
        var totalLocal = (localSummary.examsCount || 0) + (localSummary.errorNotesCount || 0) + (localSummary.growthRecordsCount || 0);
        if (totalLocal > 0) {
          wx.showModal({
            title: '检测到本地数据',
            content: '您有 ' + totalLocal + ' 条本地数据，是否同步到云端？',
            confirmText: '同步',
            cancelText: '暂不',
            success: function(res) {
              if (res.confirm) {
                that.doSync();
              }
              wx.navigateTo({ url: '/pages/onboarding/grade-select' });
            }
          });
        } else {
          wx.navigateTo({ url: '/pages/onboarding/grade-select' });
        }
      } else {
        that.refreshData();
        sync.syncAll().then(function(syncResult) {
          if (syncResult.success) {
            wx.showToast({ title: '数据已同步', icon: 'success' });
          }
        });
      }
    }).catch(function(err) {
      wx.hideLoading();
      console.warn('[Profile] login error:', err);
      wx.showToast({ title: '登录失败，请重试', icon: 'none' });
    });
  },

  doSync: function() {
    var that = this;
    wx.showLoading({ title: '同步中...' });
    sync.syncAll().then(function(result) {
      wx.hideLoading();
      if (result.success) {
        var total = (result.stats.exams || 0) + (result.stats.errorNotes || 0) + (result.stats.growthRecords || 0);
        wx.showToast({ title: '已同步 ' + total + ' 条数据', icon: 'success' });
        that.refreshData();
      } else {
        wx.showToast({ title: '同步失败，请检查网络', icon: 'none' });
      }
    });
  },

  onLogout: function() {
    wx.showModal({
      title: '确认退出',
      content: '退出后本地数据仍保留，可随时重新登录同步',
      confirmText: '确认退出',
      cancelText: '取消',
      success: function(res) {
        if (res.confirm) {
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

  onNavigateTo: function(e) {
    var url = e.currentTarget.dataset.url;
    if (url) {
      wx.navigateTo({ url: url });
    }
  },

  onUpgradeToPremium: function() {
    wx.navigateTo({ url: '/pages/profile/subscription' });
  }
});
