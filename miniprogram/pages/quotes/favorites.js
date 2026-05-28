var api = require('../../services/api');
var permission = require('../../utils/permission');
var app = getApp();

Page({
  data: {
    quotes: [],
    loading: true,
    generatingShare: false
  },

  onLoad: function() {
    this.loadFavorites();
  },

  onShow: function() {
    this.loadFavorites();
  },

  loadFavorites: function() {
    var that = this;
    api.get('/api/quotes/favorites').then(function(res) {
      that.setData({
        quotes: res.quotes || [],
        loading: false
      });
    }).catch(function() {
      that.setData({ loading: false });
    });
  },

  onUnfavorite: function(e) {
    var that = this;
    var quoteId = e.currentTarget.dataset.id;

    api.del('/api/quotes/' + quoteId + '/favorite').then(function() {
      wx.showToast({ title: '已取消收藏', icon: 'none' });
      that.loadFavorites();
    }).catch(function() {
      wx.showToast({ title: '操作失败', icon: 'none' });
    });
  },

  onShareQuote: function(e) {
    var that = this;
    var quoteId = e.currentTarget.dataset.id;

    if (that.data.generatingShare) return;

    var canShare = permission.canUse('share_quote', app.globalData.subscription);
    if (!canShare) {
      permission.showUpgradeModal('FEATURE_REQUIRES_STANDARD');
      return;
    }

    that.setData({ generatingShare: true });

    api.get('/api/quotes/' + quoteId + '/share-image').then(function(res) {
      that.setData({ generatingShare: false });
      var imageUrl = res.image_url;
      if (!imageUrl) {
        wx.showToast({ title: '图片生成失败', icon: 'none' });
        return;
      }

      wx.downloadFile({
        url: imageUrl,
        success: function(downloadRes) {
          if (downloadRes.statusCode === 200) {
            wx.saveImageToPhotosAlbum({
              filePath: downloadRes.tempFilePath,
              success: function() {
                wx.showToast({ title: '已保存到相册', icon: 'success' });
              },
              fail: function() {
                wx.previewImage({
                  urls: [downloadRes.tempFilePath],
                  current: downloadRes.tempFilePath
                });
              }
            });
          }
        },
        fail: function() {
          wx.showToast({ title: '下载失败', icon: 'none' });
        }
      });
    }).catch(function(err) {
      that.setData({ generatingShare: false });
      if (err && err.code === 'FEATURE_REQUIRES_STANDARD') {
        permission.showUpgradeModal('FEATURE_REQUIRES_STANDARD');
      } else {
        wx.showToast({ title: '生成失败', icon: 'none' });
      }
    });
  },

  onShareAppMessage: function(e) {
    var quote = e.target.dataset;
    return {
      title: quote.content || '每日金句 - 高考复习助手',
      path: '/pages/index/index'
    };
  }
});
