var api = require('../../services/api');
var permission = require('../../utils/permission');
var app = getApp();

Page({
  data: {
    year: null,
    yearOptions: [],
    yearIndex: -1,
    exporting: false,
    previewUrl: '',
    canExport: false
  },

  onLoad: function() {
    var currentYear = new Date().getFullYear();
    var years = [];
    for (var i = 0; i < 3; i++) {
      years.push({ value: currentYear - i, label: (currentYear - i) + '-' + (currentYear - i + 1) + ' 学年' });
    }
    years.unshift({ value: 0, label: '全部学年' });

    var sub = app.globalData.subscription;
    this.setData({
      yearOptions: years,
      canExport: permission.canUse('growth_export', sub)
    });
  },

  onYearChange: function(e) {
    var idx = parseInt(e.detail.value);
    var yearVal = this.data.yearOptions[idx].value;
    this.setData({
      yearIndex: idx,
      year: yearVal || null,
      previewUrl: ''
    });
  },

  onExport: function() {
    var that = this;

    if (!that.data.canExport) {
      permission.showUpgradeModal('FEATURE_REQUIRES_STANDARD');
      return;
    }

    if (that.data.exporting) return;

    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      wx.showToast({ title: '请先选择学生', icon: 'none' });
      return;
    }

    that.setData({ exporting: true });

    var params = { student_id: studentId };
    if (that.data.year) {
      params.year = that.data.year;
    }

    api.get('/api/students/' + studentId + '/growth-records/export', params).then(function(res) {
      that.setData({ exporting: false });
      var imageUrl = res.image_url;
      if (!imageUrl) {
        wx.showToast({ title: '导出失败', icon: 'none' });
        return;
      }

      that.setData({ previewUrl: imageUrl });

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
      that.setData({ exporting: false });
      if (err && err.code === 'FEATURE_REQUIRES_STANDARD') {
        permission.showUpgradeModal('FEATURE_REQUIRES_STANDARD');
      } else if (err && err.message === 'No growth records to export') {
        wx.showToast({ title: '暂无成长记录可导出', icon: 'none' });
      } else {
        wx.showToast({ title: '导出失败', icon: 'none' });
      }
    });
  },

  onUpgrade: function() {
    wx.navigateTo({ url: '/pages/profile/subscription' });
  }
});
