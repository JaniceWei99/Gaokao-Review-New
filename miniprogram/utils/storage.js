/**
 * Local storage helpers with JSON serialization.
 * Wraps wx storage APIs with try/catch for safety.
 */

module.exports = {
  /**
   * Get a value from local storage.
   * @param {string} key - Storage key
   * @returns {*} Parsed value, or null if not found
   */
  get(key) {
    try {
      const value = wx.getStorageSync(key);
      if (value === '' || value === undefined) return null;
      return value;
    } catch (e) {
      console.warn('[Storage] get error:', key, e);
      return null;
    }
  },

  /**
   * Set a value in local storage.
   * @param {string} key - Storage key
   * @param {*} value - Value to store (will be serialized automatically by wx)
   */
  set(key, value) {
    try {
      wx.setStorageSync(key, value);
    } catch (e) {
      console.warn('[Storage] set error:', key, e);
    }
  },

  /**
   * Remove a value from local storage.
   * @param {string} key - Storage key
   */
  remove(key) {
    try {
      wx.removeStorageSync(key);
    } catch (e) {
      console.warn('[Storage] remove error:', key, e);
    }
  },

  /**
   * Clear all local storage.
   */
  clear() {
    try {
      wx.clearStorageSync();
    } catch (e) {
      console.warn('[Storage] clear error:', e);
    }
  }
};
