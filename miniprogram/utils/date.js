/**
 * Date utility functions.
 */

/**
 * Calculate the number of days remaining until a given date.
 * @param {string} dateStr - Date string (e.g., '2026-06-07')
 * @returns {number} Days remaining (negative if in the past)
 */
function daysUntil(dateStr) {
  const target = new Date(dateStr);
  const now = new Date();
  // Reset time to midnight for accurate day calculation
  target.setHours(0, 0, 0, 0);
  now.setHours(0, 0, 0, 0);
  const diffMs = target.getTime() - now.getTime();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}

/**
 * Format a date string to Chinese display format.
 * @param {string} dateStr - Date string (e.g., '2026-06-07')
 * @returns {string} Formatted date (e.g., '2026年6月7日')
 */
function formatDate(dateStr) {
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return year + '年' + month + '月' + day + '日';
}

/**
 * Format a date as a relative string.
 * @param {string} dateStr - Date string
 * @returns {string} Relative string (e.g., '47天后', '3天前', '今天')
 */
function formatRelative(dateStr) {
  const days = daysUntil(dateStr);
  if (days === 0) return '今天';
  if (days > 0) return days + '天后';
  return Math.abs(days) + '天前';
}

/**
 * Get the current school year string.
 * School year starts in September.
 * @returns {string} e.g., '2025-2026'
 */
function getSchoolYear() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1; // 1-12
  // If before September, school year started last year
  if (month < 9) {
    return (year - 1) + '-' + year;
  }
  return year + '-' + (year + 1);
}

/**
 * Check if a date is in the past.
 * @param {string} dateStr - Date string
 * @returns {boolean}
 */
function isPast(dateStr) {
  return daysUntil(dateStr) < 0;
}

/**
 * Format date to short format (MM-DD).
 * @param {string} dateStr - Date string
 * @returns {string} e.g., '06-07'
 */
function formatShort(dateStr) {
  const date = new Date(dateStr);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return month + '-' + day;
}

/**
 * Format date to YYYY-MM-DD string.
 * @param {Date} [date] - Date object (defaults to now)
 * @returns {string} e.g., '2026-06-07'
 */
function toDateString(date) {
  const d = date || new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return year + '-' + month + '-' + day;
}

module.exports = {
  daysUntil,
  formatDate,
  formatRelative,
  getSchoolYear,
  isPast,
  formatShort,
  toDateString
};
