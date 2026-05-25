/**
 * Subscription plan constants.
 */

module.exports = {
  PLANS: {
    free: { name: '免费版', price: 0 },
    standard: {
      name: '标准版',
      monthly: 19.9,
      yearly: 199,
      lifetime: 399,
      features: [
        '里程碑行动卡片',
        '完整金句库300+条',
        '金句收藏与分享',
        '知识点三级展开',
        '无限错题存储',
        '无限成长记录',
        '成绩趋势分析',
        '成长档案导出'
      ]
    },
    premium: {
      name: '高级版',
      monthly: 39.9,
      yearly: 399,
      features: [
        '标准版全部功能',
        'AI家长顾问',
        'AI个性化行动建议',
        'AI个性化金句',
        'AI错题分类助手',
        'AI月度成长报告'
      ]
    }
  },
  FREE_LIMITS: {
    error_notes: 10,
    growth_records: 5,
    exams: 3,
    quotes: 50
  }
};
