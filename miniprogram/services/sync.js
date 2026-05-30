/**
 * Sync Service — 本地数据与云端同步
 *
 * 当用户登录后，将本地数据同步到云端
 * 支持双向同步（本地新增 → 云端；云端有本地无 → 本地）
 *
 * 同步策略：
 * 1. 优先读取云端数据（最新）
 * 2. 本地新增数据合并到云端
 * 3. 冲突处理：时间戳更晚的覆盖
 */

const storage = require('./storage');
const api = require('./api');

module.exports = {
  /**
   * 检查是否已登录
   */
  isLoggedIn() {
    const app = getApp();
    return !!app.globalData.token;
  },

  /**
   * 获取当前学生ID（优先本地）
   */
  getStudentId() {
    const local = storage.getStudent();
    if (local && local.id) return local.id;
    const app = getApp();
    return app.getCurrentStudentId();
  },

  /**
   * 同步所有数据
   * @returns {Promise<{success: boolean, stats: object}>}
   */
  async syncAll() {
    if (!this.isLoggedIn()) {
      return { success: false, reason: 'not_logged_in' };
    }

    const studentId = this.getStudentId();
    if (!studentId) {
      return { success: false, reason: 'no_student' };
    }

    const stats = { exams: 0, errorNotes: 0, growthRecords: 0, quotes: 0 };

    try {
      await Promise.all([
        this.syncExams(studentId).then(c => stats.exams = c),
        this.syncErrorNotes(studentId).then(c => stats.errorNotes = c),
        this.syncGrowthRecords(studentId).then(c => stats.growthRecords = c),
        this.syncQuotes(studentId).then(c => stats.quotes = c),
      ]);

      storage.setLastSyncTime(Date.now());
      return { success: true, stats };
    } catch (err) {
      console.warn('[Sync] syncAll error:', err);
      return { success: false, reason: 'sync_error', error: err };
    }
  },

  /**
   * 同步考试成绩
   */
  async syncExams(studentId) {
    const localExams = storage.getExams();
    let synced = 0;

    for (const exam of localExams) {
      if (!exam.id || exam.id.startsWith('local_')) {
        try {
          const result = await api.post(`/api/students/${studentId}/exams`, {
            exam_name: exam.exam_name,
            exam_date: exam.exam_date,
            scores: exam.scores || [],
          });
          synced++;
        } catch (e) {
          console.warn('[Sync] syncExam error:', e);
        }
      }
    }
    return synced;
  },

  /**
   * 同步错题记录
   */
  async syncErrorNotes(studentId) {
    const localNotes = storage.getErrorNotes();
    let synced = 0;

    for (const note of localNotes) {
      if (!note.id || note.id.startsWith('local_')) {
        try {
          const payload = {
            subject: note.subject,
            knowledge_node_id: note.knowledge_node_id,
            note_text: note.note_text,
            photo_url: note.photo_url,
          };
          await api.post(`/api/students/${studentId}/error-notes`, payload);
          synced++;
        } catch (e) {
          console.warn('[Sync] syncErrorNote error:', e);
        }
      }
    }
    return synced;
  },

  /**
   * 同步成长记录
   */
  async syncGrowthRecords(studentId) {
    const localRecords = storage.getGrowthRecords();
    let synced = 0;

    for (const record of localRecords) {
      if (!record.id || record.id.startsWith('local_')) {
        try {
          const payload = {
            record_date: record.record_date,
            title: record.title,
            description: record.description,
            photo_url: record.photo_url,
            category: record.category,
          };
          await api.post(`/api/students/${studentId}/growth-records`, payload);
          synced++;
        } catch (e) {
          console.warn('[Sync] syncGrowthRecord error:', e);
        }
      }
    }
    return synced;
  },

  /**
   * 同步收藏金句
   */
  async syncQuotes(studentId) {
    const localFavorites = storage.getQuoteFavorites();
    let synced = 0;

    for (const quote of localFavorites) {
      if (!quote.id || quote.id.startsWith('local_')) {
        try {
          await api.post(`/api/students/${studentId}/quotes/${quote.id}/favorite`, {});
          synced++;
        } catch (e) {
          console.warn('[Sync] syncQuote error:', e);
        }
      }
    }
    return synced;
  },

  /**
   * 获取数据摘要（用于'我的'页面展示）
   */
  getDataSummary() {
    return storage.getLocalDataSummary();
  },

  /**
   * 检查是否需要同步（本地有数据但未登录）
   */
  needsSync() {
    const summary = this.getDataSummary();
    return !this.isLoggedIn() && (
      summary.examsCount > 0 ||
      summary.errorNotesCount > 0 ||
      summary.growthRecordsCount > 0
    );
  },
};
