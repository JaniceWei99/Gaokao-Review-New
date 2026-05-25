// pages/growth/timeline.js — Growth Records Timeline
const api = require('../../services/api');
const dateUtil = require('../../utils/date');

const app = getApp();

const CATEGORIES = [
  { key: 'certificate', name: '证书奖状' },
  { key: 'volunteer', name: '志愿活动' },
  { key: 'competition', name: '竞赛成绩' },
  { key: 'art', name: '文艺体育' },
  { key: 'research', name: '研究项目' },
  { key: 'other', name: '其他' }
];

Page({
  data: {
    categories: CATEGORIES,
    currentCategory: '',
    records: [],
    loading: false,
    page: 1,
    hasMore: true
  },

  onLoad() {
    this.loadRecords();
  },

  onShow() {
    if (this._needRefresh) {
      this._needRefresh = false;
      this.setData({ page: 1, records: [], hasMore: true });
      this.loadRecords();
    }
  },

  /**
   * Filter by category.
   */
  onFilterCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({
      currentCategory: category,
      page: 1,
      records: [],
      hasMore: true
    });
    this.loadRecords();
  },

  /**
   * Load growth records from backend.
   */
  async loadRecords() {
    const studentId = app.getCurrentStudentId();
    if (!studentId) return;

    this.setData({ loading: true });

    try {
      const params = {
        page: this.data.page,
        page_size: 20
      };

      if (this.data.currentCategory) {
        params.category = this.data.currentCategory;
      }

      const res = await api.get('/api/students/' + studentId + '/growth-records', params);
      const records = (res.data || res || []).map(function(item) {
        const categoryObj = CATEGORIES.find(function(c) { return c.key === item.category; });
        return {
          ...item,
          category_name: categoryObj ? categoryObj.name : item.category,
          date_display: item.date ? dateUtil.formatDate(item.date) : ''
        };
      });

      this.setData({
        records: this.data.page === 1 ? records : this.data.records.concat(records),
        hasMore: records.length >= 20,
        loading: false
      });
    } catch (err) {
      console.warn('[Growth] load error:', err);
      this.setData({ loading: false });
    }
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 });
      this.loadRecords();
    }
  }
});
