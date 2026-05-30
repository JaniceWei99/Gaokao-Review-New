/**
 * Storage Service — 本地优先的数据存储抽象层
 *
 * 所有数据读写通过此模块，不直接调用 wx.setStorage/getStorage
 * 支持本地优先、云端同步的双写策略
 *
 * 数据结构：
 * - exams:        考试成绩列表
 * - errorNotes:   错题列表
 * - growthRecords: 成长记录列表
 * - student:      当前学生信息
 * - quoteFavorites: 收藏的金句列表
 * - milestoneSettings: 里程碑提醒设置
 * - lastSyncTime: 最后同步时间
 */

const api = require('./api');

const KEYS = {
  EXAMS: 'local_exams',
  ERROR_NOTES: 'local_error_notes',
  GROWTH_RECORDS: 'local_growth_records',
  STUDENT: 'local_student',
  QUOTE_FAVORITES: 'local_quote_favorites',
  MILESTONE_SETTINGS: 'local_milestone_settings',
  LAST_SYNC: 'local_last_sync_time',
  QUOTE_HISTORY: 'local_quote_history',
  DAILY_QUOTE: 'local_daily_quote',
};

function get(key) {
  try {
    const data = wx.getStorageSync(key);
    return data || null;
  } catch (e) {
    console.warn('[Storage] get error:', key, e);
    return null;
  }
}

function set(key, value) {
  try {
    wx.setStorageSync(key, value);
    return true;
  } catch (e) {
    console.warn('[Storage] set error:', key, e);
    return false;
  }
}

function remove(key) {
  try {
    wx.removeStorageSync(key);
    return true;
  } catch (e) {
    return false;
  }
}

function clear() {
  try {
    wx.clearStorageSync();
    return true;
  } catch (e) {
    return false;
  }
}

module.exports = {
  KEYS,

  getExams() {
    return get(KEYS.EXAMS) || [];
  },

  saveExam(exam) {
    const exams = this.getExams();
    const existingIndex = exams.findIndex(e => e.id === exam.id);
    if (existingIndex >= 0) {
      exams[existingIndex] = { ...exams[existingIndex], ...exam, _localUpdated: Date.now() };
    } else {
      exams.unshift({ ...exam, id: exam.id || 'local_' + Date.now(), _localCreated: Date.now() });
    }
    set(KEYS.EXAMS, exams);
    return exam;
  },

  deleteExam(examId) {
    const exams = this.getExams().filter(e => e.id !== examId);
    set(KEYS.EXAMS, exams);
  },

  getErrorNotes() {
    return get(KEYS.ERROR_NOTES) || [];
  },

  saveErrorNote(note) {
    const notes = this.getErrorNotes();
    const existingIndex = notes.findIndex(n => n.id === note.id);
    if (existingIndex >= 0) {
      notes[existingIndex] = { ...notes[existingIndex], ...note, _localUpdated: Date.now() };
    } else {
      notes.unshift({ ...note, id: note.id || 'local_' + Date.now(), _localCreated: Date.now() });
    }
    set(KEYS.ERROR_NOTES, notes);
    return note;
  },

  deleteErrorNote(noteId) {
    const notes = this.getErrorNotes().filter(n => n.id !== noteId);
    set(KEYS.ERROR_NOTES, notes);
  },

  getGrowthRecords() {
    return get(KEYS.GROWTH_RECORDS) || [];
  },

  saveGrowthRecord(record) {
    const records = this.getGrowthRecords();
    const existingIndex = records.findIndex(r => r.id === record.id);
    if (existingIndex >= 0) {
      records[existingIndex] = { ...records[existingIndex], ...record, _localUpdated: Date.now() };
    } else {
      records.unshift({ ...record, id: record.id || 'local_' + Date.now(), _localCreated: Date.now() });
    }
    set(KEYS.GROWTH_RECORDS, records);
    return record;
  },

  deleteGrowthRecord(recordId) {
    const records = this.getGrowthRecords().filter(r => r.id !== recordId);
    set(KEYS.GROWTH_RECORDS, records);
  },

  getStudent() {
    return get(KEYS.STUDENT) || null;
  },

  saveStudent(student) {
    set(KEYS.STUDENT, { ...student, _localUpdated: Date.now() });
    return student;
  },

  getQuoteFavorites() {
    return get(KEYS.QUOTE_FAVORITES) || [];
  },

  saveQuoteFavorite(quote) {
    const favorites = this.getQuoteFavorites();
    const exists = favorites.some(q => q.id === quote.id);
    if (!exists) {
      favorites.unshift({ ...quote, _localCreated: Date.now() });
      set(KEYS.QUOTE_FAVORITES, favorites);
    }
    return quote;
  },

  removeQuoteFavorite(quoteId) {
    const favorites = this.getQuoteFavorites().filter(q => q.id !== quoteId);
    set(KEYS.QUOTE_FAVORITES, favorites);
  },

  getDailyQuote() {
    return get(KEYS.DAILY_QUOTE) || null;
  },

  saveDailyQuote(quote) {
    set(KEYS.DAILY_QUOTE, { ...quote, date: new Date().toDateString() });
  },

  getMilestoneSettings() {
    return get(KEYS.MILESTONE_SETTINGS) || {};
  },

  saveMilestoneSetting(milestoneId, settings) {
    const all = this.getMilestoneSettings();
    all[milestoneId] = { ...settings, _localUpdated: Date.now() };
    set(KEYS.MILESTONE_SETTINGS, all);
  },

  getLastSyncTime() {
    return get(KEYS.LAST_SYNC) || null;
  },

  setLastSyncTime(time) {
    set(KEYS.LAST_SYNC, time || Date.now());
  },

  getLocalDataSummary() {
    return {
      examsCount: this.getExams().length,
      errorNotesCount: this.getErrorNotes().length,
      growthRecordsCount: this.getGrowthRecords().length,
      quoteFavoritesCount: this.getQuoteFavorites().length,
      lastSyncTime: this.getLastSyncTime(),
      hasStudent: !!this.getStudent(),
    };
  },

  clear,
  get,
  set,
  remove,
};
