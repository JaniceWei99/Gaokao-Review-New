var app = getApp();
var storage = require('../../services/storage');
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
    currentSchoolYear: '',
    schoolYears: [],
    records: [],
    loading: false,
    source: 'local',
    isLoggedIn: false
  },

  onLoad: function() {
    this.setData({ isLoggedIn: app.isLoggedIn() });
    this._loadRecords();
  },

  onShow: function() {
    var loggedIn = app.isLoggedIn();
    if (this._needRefresh || this.data.isLoggedIn !== loggedIn) {
      this._needRefresh = false;
      this.setData({ isLoggedIn: loggedIn });
      this._loadRecords();
    }
  },

  onHide: function() {
    this._needRefresh = true;
  },

  onFilterType: function(e) {
    var type = e.currentTarget.dataset.type;
    this.setData({ currentType: type });
    this._loadRecords();
  },

  onSwitchSchoolYear: function(e) {
    var year = e.currentTarget.dataset.year;
    this.setData({ currentSchoolYear: year });
  },

  _loadRecords: function() {
    var local = storage.getGrowthRecords();
    var filteredLocal = this._filterByType(local);

    if (filteredLocal.length > 0) {
      var schoolYears = this._extractSchoolYears(local);
      this.setData({
        records: this._processRecords(filteredLocal),
        schoolYears: schoolYears,
        loading: false,
        source: 'local',
        isLoggedIn: app.isLoggedIn()
      });
    } else {
      this.setData({ loading: false, isLoggedIn: app.isLoggedIn() });
    }

    if (app.isLoggedIn()) {
      this._loadFromCloud();
    }
  },

  _loadFromCloud: function() {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId) return;

    that.setData({ loading: true });

    var params = { page: 1, page_size: 100 };

    growthService.listGrowthRecords(studentId, params).then(function(res) {
      var cloud = (res.growth_records || []);
      cloud.forEach(function(r) {
        storage.saveGrowthRecord({
          id: r.id,
          record_type: r.record_type,
          title: r.title,
          description: r.description,
          record_date: r.record_date,
          category: r.category,
          awarding_body: r.awarding_body,
          image_url: r.image_url,
          auto_generated: r.auto_generated
        });
      });

      var merged = storage.getGrowthRecords();
      var filteredMerged = that._filterByType(merged);
      var schoolYears = that._extractSchoolYears(merged);

      that.setData({
        records: that._processRecords(filteredMerged),
        schoolYears: schoolYears,
        loading: false,
        source: cloud.length > 0 ? 'cloud' : 'local'
      });
    }).catch(function(err) {
      console.warn('[GrowthTimeline] cloud load error:', err);
      that.setData({ loading: false });
    });
  },

  _filterByType: function(records) {
    var type = this.data.currentType;
    if (!type) return records;
    return records.filter(function(r) { return r.record_type === type; });
  },

  _extractSchoolYears: function(records) {
    var years = {};
    records.forEach(function(r) {
      if (r.record_date) {
        var date = new Date(r.record_date);
        var month = date.getMonth();
        var year = date.getFullYear();
        var schoolYear = month >= 8 ? (year + '-' + (year + 1)) : ((year - 1) + '-' + year);
        years[schoolYear] = true;
      }
    });
    return Object.keys(years).sort().reverse();
  },

  _processRecords: function(records) {
    return records.map(function(item) {
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
        auto_generated: item.auto_generated
      };
    });
  },

  onDeleteRecord: function(e) {
    var that = this;
    var recordId = e.currentTarget.dataset.id;
    var studentId = app.getCurrentStudentId();

    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除这条记录吗？',
      success: function(res) {
        if (res.confirm) {
          storage.deleteGrowthRecord(recordId);
          var remaining = storage.getGrowthRecords();
          var filtered = that._filterByType(remaining);
          that.setData({
            records: that._processRecords(filtered),
            schoolYears: that._extractSchoolYears(remaining)
          });
          wx.showToast({ title: '已删除', icon: 'success' });

          if (app.isLoggedIn() && studentId) {
            growthService.deleteGrowthRecord(studentId, recordId).catch(function() {});
          }
        }
      }
    });
  },

  onGoToAdd: function() {
    wx.navigateTo({ url: '/pages/growth/add' });
  }
});