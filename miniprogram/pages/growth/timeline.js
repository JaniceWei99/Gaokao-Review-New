var app = getApp();
var growthService = require('../../services/growth');
var dateUtil = require('../../utils/date');

var RECORD_TYPE_MAP = {
  award: '🏆 获奖',
  progress: '📈 进步',
  performance: '🎭 演出',
  breakthrough: '💡 突破',
  memo: '📝 备忘'
};

Page({
  data: {
    currentType: '',
    records: [],
    schoolYears: [],
    currentSchoolYear: '',
    loading: false,
    page: 1,
    hasMore: true
  },

  onLoad: function() {
    this._loadRecords();
  },

  onShow: function() {
    if (this._needRefresh) {
      this._needRefresh = false;
      this.setData({ page: 1, records: [], hasMore: true });
      this._loadRecords();
    }
  },

  onHide: function() {
    this._needRefresh = true;
  },

  onFilterType: function(e) {
    var type = e.currentTarget.dataset.type;
    this.setData({
      currentType: type,
      page: 1,
      records: [],
      hasMore: true
    });
    this._loadRecords();
  },

  onSwitchSchoolYear: function(e) {
    var year = e.currentTarget.dataset.year;
    this.setData({
      currentSchoolYear: year,
      page: 1,
      records: [],
      hasMore: true
    });
    this._loadRecords();
  },

  _loadRecords: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    that.setData({ loading: true });

    var params = {
      page: that.data.page,
      page_size: 50
    };

    if (that.data.currentType) {
      params.record_type = that.data.currentType;
    }

    if (that.data.currentSchoolYear) {
      var yearInt = parseInt(that.data.currentSchoolYear.split('-')[0], 10);
      params.year = yearInt;
    }

    growthService.listGrowthRecords(studentId, params).then(function(res) {
      var records = (res.growth_records || []).map(function(item) {
        return {
          id: item.id,
          record_type: item.record_type,
          type_label: RECORD_TYPE_MAP[item.record_type] || item.record_type,
          title: item.title,
          description: item.description,
          record_date: item.record_date,
          date_display: item.record_date ? dateUtil.formatDate(item.record_date) : '',
          category: item.category,
          awarding_body: item.awarding_body,
          image_url: item.image_url,
          linked_quote_id: item.linked_quote_id,
          auto_generated: item.auto_generated
        };
      });

      var schoolYears = [];
      if (res.by_school_year) {
        schoolYears = Object.keys(res.by_school_year).sort().reverse();
      }

      that.setData({
        records: that.data.page === 1 ? records : that.data.records.concat(records),
        hasMore: records.length >= 50,
        loading: false,
        schoolYears: schoolYears.length > 0 ? schoolYears : that.data.schoolYears
      });
    }).catch(function(err) {
      console.warn('[GrowthTimeline] load error:', err);
      that.setData({ loading: false });
    });
  },

  onReachBottom: function() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 });
      this._loadRecords();
    }
  },

  onGoToAdd: function() {
    wx.navigateTo({ url: '/pages/growth/add' });
  },

  onDeleteRecord: function(e) {
    var that = this;
    var recordId = e.currentTarget.dataset.id;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除这条记录吗？',
      success: function(res) {
        if (res.confirm) {
          growthService.deleteGrowthRecord(studentId, recordId).then(function() {
            wx.showToast({ title: '已删除', icon: 'success' });
            that.setData({ page: 1, records: [], hasMore: true });
            that._loadRecords();
          }).catch(function() {
            wx.showToast({ title: '删除失败', icon: 'none' });
          });
        }
      }
    });
  }
});
