// pages/errors/list.js — Error Notes List
const api = require('../../services/api');
const { ALL_SUBJECTS } = require('../../constants/subjects');
const dateUtil = require('../../utils/date');

const app = getApp();

Page({
  data: {
    subjects: ALL_SUBJECTS,
    currentSubject: '',
    currentStatus: '',
    errorNotes: [],
    loading: false,
    page: 1,
    hasMore: true
  },

  onLoad() {
    this.loadErrorNotes();
  },

  onShow() {
    // Refresh list when returning from add/detail
    if (this._needRefresh) {
      this._needRefresh = false;
      this.loadErrorNotes();
    }
  },

  /**
   * Filter by subject.
   */
  onFilterSubject(e) {
    const subject = e.currentTarget.dataset.subject;
    this.setData({
      currentSubject: subject,
      page: 1,
      errorNotes: [],
      hasMore: true
    });
    this.loadErrorNotes();
  },

  /**
   * Filter by status.
   */
  onFilterStatus(e) {
    const status = e.currentTarget.dataset.status;
    this.setData({
      currentStatus: status,
      page: 1,
      errorNotes: [],
      hasMore: true
    });
    this.loadErrorNotes();
  },

  /**
   * Load error notes from backend.
   */
  async loadErrorNotes() {
    const studentId = app.getCurrentStudentId();
    if (!studentId) return;

    this.setData({ loading: true });

    try {
      const params = {
        page: this.data.page,
        page_size: 20
      };

      if (this.data.currentSubject) {
        params.subject = this.data.currentSubject;
      }
      if (this.data.currentStatus) {
        params.status = this.data.currentStatus;
      }

      const res = await api.get('/api/students/' + studentId + '/error-notes', params);
      const notes = (res.data || res || []).map(function(item) {
        return {
          ...item,
          created_at_display: item.created_at ? dateUtil.formatDate(item.created_at) : ''
        };
      });

      this.setData({
        errorNotes: this.data.page === 1 ? notes : this.data.errorNotes.concat(notes),
        hasMore: notes.length >= 20,
        loading: false
      });
    } catch (err) {
      console.warn('[ErrorList] load error:', err);
      this.setData({ loading: false });
    }
  },

  /**
   * Load more (infinite scroll).
   */
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 });
      this.loadErrorNotes();
    }
  }
});
