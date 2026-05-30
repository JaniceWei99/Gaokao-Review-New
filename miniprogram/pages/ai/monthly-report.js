var api = require('../../services/api');
var app = getApp();

Page({
  data: {
    report: null,
    loading: true,
    year: 0,
    month: 0,
    studentId: null
  },

  onLoad: function(options) {
    var studentId = app.getCurrentStudentId();
    if (!studentId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    var now = new Date();
    var year = options.year ? parseInt(options.year) : now.getFullYear();
    var month = options.month ? parseInt(options.month) : now.getMonth() + 1;

    this.setData({
      studentId: studentId,
      year: year,
      month: month
    });

    this.loadReport();
  },

  loadReport: function() {
    var that = this;
    var studentId = that.data.studentId;
    var year = that.data.year;
    var month = that.data.month;

    that.setData({ loading: true });

    api.get('/api/students/' + studentId + '/ai/monthly-report', {
      year: year,
      month: month
    }).then(function(res) {
      that.setData({
        report: res,
        loading: false
      });
    }).catch(function(err) {
      console.warn('[Monthly Report] load error:', err);
      that.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    });
  },

  onPrevMonth: function() {
    var year = this.data.year;
    var month = this.data.month;
    month--;
    if (month < 1) {
      month = 12;
      year--;
    }
    this.setData({ year: year, month: month });
    this.loadReport();
  },

  onNextMonth: function() {
    var year = this.data.year;
    var month = this.data.month;
    var now = new Date();
    month++;
    if (month > 12) {
      month = 1;
      year++;
    }
    if (year > now.getFullYear() || (year === now.getFullYear() && month > now.getMonth() + 1)) {
      wx.showToast({ title: '不能查看未来月份', icon: 'none' });
      return;
    }
    this.setData({ year: year, month: month });
    this.loadReport();
  },

  onShareReport: function() {
    var that = this;
    var report = that.data.report;
    if (!report) return;

    wx.showActionSheet({
      itemList: ['转发给朋友', '生成分享图片'],
      success: function(res) {
        if (res.tapIndex === 0) {
          wx.showShareMenu({ withShareTicket: true });
        } else if (res.tapIndex === 1) {
          wx.showToast({ title: '图片生成功能开发中', icon: 'none' });
        }
      }
    });
  },

  onShareAppMessage: function() {
    var report = this.data.report;
    var title = report ? (report.title || '月度成长报告') : '月度成长报告';
    return {
      title: title + ' - 高考家长帮',
      path: '/pages/index/index'
    };
  }
});
