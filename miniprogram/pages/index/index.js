// pages/index/index.js — Homepage
const api = require('../../services/api');
const auth = require('../../services/auth');
const dateUtil = require('../../utils/date');

const app = getApp();

// Shanghai Gaokao date (first day)
const GAOKAO_DATE = '2026-06-07';

Page({
  data: {
    quote: '',
    quoteSource: '',
    countdown: '--',
    gaokaoDate: dateUtil.formatDate(GAOKAO_DATE),
    milestones: [],
    loading: true
  },

  onLoad() {
    this.updateCountdown();
    this.loadDashboard();
  },

  onShow() {
    this.updateCountdown();
  },

  onPullDownRefresh() {
    this.loadDashboard().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * Update the Gaokao countdown.
   */
  updateCountdown() {
    const days = dateUtil.daysUntil(GAOKAO_DATE);
    this.setData({
      countdown: days > 0 ? days : 0
    });
  },

  /**
   * Load dashboard data from backend.
   */
  async loadDashboard() {
    // Check if logged in
    if (!app.isLoggedIn()) {
      this.setData({ loading: false });
      return;
    }

    const studentId = app.getCurrentStudentId();
    if (!studentId) {
      this.setData({ loading: false });
      return;
    }

    try {
      this.setData({ loading: true });

      // Load daily quote
      this.loadQuote();

      // Load milestones
      const milestonesRes = await api.get('/api/students/' + studentId + '/milestones', {
        current: true,
        limit: 3
      }, { showError: false });

      const milestones = (milestonesRes.data || milestonesRes || []).map(function(item) {
        return {
          ...item,
          date_display: item.date ? dateUtil.formatRelative(item.date) : ''
        };
      });

      this.setData({
        milestones: milestones,
        loading: false
      });
    } catch (err) {
      console.warn('[Home] loadDashboard error:', err);
      this.setData({ loading: false });
    }
  },

  /**
   * Load daily quote.
   */
  async loadQuote() {
    try {
      const res = await api.get('/api/quotes/daily', {}, { showError: false });
      if (res && res.content) {
        this.setData({
          quote: res.content,
          quoteSource: res.source ? ('— ' + res.source) : ''
        });
      }
    } catch (err) {
      // Use default quote on error
      this.setData({
        quote: '每一天的努力，都是在为未来铺路。',
        quoteSource: ''
      });
    }
  }
});
