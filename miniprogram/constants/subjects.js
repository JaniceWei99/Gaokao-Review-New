/**
 * Subject constants for Shanghai Gaokao.
 * Required: 语文, 数学, 外语 (3+3 model)
 * Elective: Choose 3 from 6
 */

module.exports = {
  ALL_SUBJECTS: [
    { id: 'chinese', name: '语文', category: 'required' },
    { id: 'math', name: '数学', category: 'required' },
    { id: 'english', name: '外语', category: 'required' },
    { id: 'physics', name: '物理', category: 'elective' },
    { id: 'chemistry', name: '化学', category: 'elective' },
    { id: 'biology', name: '生命科学', category: 'elective' },
    { id: 'politics', name: '政治', category: 'elective' },
    { id: 'history', name: '历史', category: 'elective' },
    { id: 'geography', name: '地理', category: 'elective' }
  ],
  REQUIRED_SUBJECTS: ['chinese', 'math', 'english'],
  ELECTIVE_SUBJECTS: ['physics', 'chemistry', 'biology', 'politics', 'history', 'geography']
};
