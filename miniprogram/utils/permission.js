/**
 * Permission utility — check plan limits and show upgrade prompts.
 */

var plans = require('../constants/plans');

var UPGRADE_MESSAGES = {
  FREE_LIMIT_ERROR_NOTES: {
    title: '错题本已满',
    message: '免费版最多保存10道错题，升级标准版解锁无限存储',
  },
  FREE_LIMIT_GROWTH: {
    title: '成长册已满',
    message: '免费版最多保存5条成长记录，升级标准版继续记录闪光时刻',
  },
  FREE_LIMIT_EXAMS: {
    title: '成绩记录已满',
    message: '免费版最多记录3次考试，升级标准版查看趋势分析',
  },
  FEATURE_REQUIRES_STANDARD: {
    title: '标准版功能',
    message: '此功能需要标准版，升级后即可使用',
  },
  FEATURE_REQUIRES_PREMIUM: {
    title: '高级版功能',
    message: '此功能需要高级版，升级后即可使用',
  },
};

/**
 * Check if a feature is available under the current plan.
 * @param {string} feature - Feature key
 * @param {Object} subscription - Current subscription object from API
 * @returns {boolean}
 */
function canUse(feature, subscription) {
  if (!subscription) return false;
  var limits = subscription.limits || {};
  var plan = subscription.plan || 'free';

  switch (feature) {
    case 'knowledge_l3':
      return limits.can_expand_knowledge_l3 === true;
    case 'share_quote':
      return limits.can_share_quote_image === true;
    case 'widget':
      return limits.can_use_widget === true;
    case 'export_growth':
      return limits.can_export_growth === true;
    case 'exam_trend':
      return limits.can_view_exam_trend === true;
    case 'action_cards':
      return limits.has_action_cards === true;
    case 'unlimited_errors':
      return plan !== 'free';
    case 'unlimited_growth':
      return plan !== 'free';
    case 'unlimited_exams':
      return plan !== 'free';
    default:
      return true;
  }
}

/**
 * Show an upgrade modal with contextual message.
 * @param {string} errorCode - Error code from API (e.g., 'FREE_LIMIT_ERROR_NOTES')
 * @param {Function} [onConfirm] - Callback when user taps "upgrade"
 * @param {Function} [onCancel] - Callback when user dismisses
 */
function showUpgradeModal(errorCode, onConfirm, onCancel) {
  var msg = UPGRADE_MESSAGES[errorCode] || UPGRADE_MESSAGES.FEATURE_REQUIRES_STANDARD;

  wx.showModal({
    title: msg.title,
    content: msg.message,
    cancelText: '下次再说',
    confirmText: '去升级',
    success: function(res) {
      if (res.confirm) {
        if (onConfirm) {
          onConfirm();
        } else {
          wx.navigateTo({ url: '/pages/profile/subscription' });
        }
      } else if (onCancel) {
        onCancel();
      }
    }
  });
}

/**
 * Check usage against free limits and show prompt if needed.
 * @param {string} feature - 'error_notes' | 'growth_records' | 'exams'
 * @param {number} used - Current usage count
 * @returns {boolean} true if under limit, false if at limit
 */
function checkFreeLimit(feature, used) {
  var limits = plans.FREE_LIMITS || {};
  var max = limits[feature];

  if (max === undefined || used < max) return true;

  var errorCode;
  if (feature === 'error_notes') errorCode = 'FREE_LIMIT_ERROR_NOTES';
  else if (feature === 'growth_records') errorCode = 'FREE_LIMIT_GROWTH';
  else if (feature === 'exams') errorCode = 'FREE_LIMIT_EXAMS';
  else return true;

  showUpgradeModal(errorCode);
  return false;
}

module.exports = {
  canUse: canUse,
  showUpgradeModal: showUpgradeModal,
  checkFreeLimit: checkFreeLimit,
  UPGRADE_MESSAGES: UPGRADE_MESSAGES,
};
