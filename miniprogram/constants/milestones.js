var now = new Date();
var year = now.getFullYear();

function d(month, day, offsetYear) {
  var y = year + (offsetYear || 0);
  var date = new Date(y, month - 1, day);
  if (date < now) {
    date = new Date(y + 1, month - 1, day);
  }
  var m = String(date.getMonth() + 1).padStart(2, '0');
  var dd = String(date.getDate()).padStart(2, '0');
  return date.getFullYear() + '-' + m + '-' + dd;
}

function d3(month, day) {
  var y = month >= 9 ? year - 1 : year;
  var m = String(month).padStart(2, '0');
  var dd = String(day).padStart(2, '0');
  return y + '-' + m + '-' + dd;
}

var GAO3_MILESTONES = [
  { id: 'g3_01', name: '高考大报名', event_date: d3(10, 14), category: 'registration', type: 'system' },
  { id: 'g3_03', name: '外语听说测试', event_date: d3(11, 25), category: 'autumn_exam', type: 'system' },
  { id: 'g3_04', name: '一模', event_date: d3(12, 8), category: 'mock_exam', type: 'system' },
  { id: 'g3_06', name: '春季高考（含外语一考）', event_date: d3(1, 3), category: 'spring_exam', type: 'system' },
  { id: 'g3_07', name: '春考成绩公布', event_date: d3(1, 25), category: 'result_release', type: 'system' },
  { id: 'g3_08', name: '春考志愿填报', event_date: d3(1, 30), category: 'volunteer_fill', type: 'system' },
  { id: 'g3_09', name: '春招院校自主测试', event_date: d3(2, 28), category: 'spring_exam', type: 'system' },
  { id: 'g3_10', name: '二模', event_date: d3(3, 15), category: 'mock_exam', type: 'system' },
  { id: 'g3_11', name: '综合评价报名', event_date: d3(4, 1), category: 'comprehensive_eval', type: 'system' },
  { id: 'g3_12', name: '三模', event_date: d3(4, 15), category: 'mock_exam', type: 'system' },
  { id: 'g3_13', name: '等级考（小三门）', event_date: d3(5, 4), category: 'level_exam', type: 'system' },
  { id: 'g3_14', name: '等级考技能操作测试', event_date: d3(5, 19), category: 'level_exam', type: 'system' },
  { id: 'g3_15', name: '高考语文+数学', event_date: d3(6, 7), category: 'autumn_exam', type: 'system' },
  { id: 'g3_16', name: '高考外语笔试', event_date: d3(6, 8), category: 'autumn_exam', type: 'system' },
  { id: 'g3_17', name: '高考外语听说', event_date: d3(6, 9), category: 'autumn_exam', type: 'system' },
  { id: 'g3_18', name: '成绩公布', event_date: d3(6, 23), category: 'result_release', type: 'system' },
  { id: 'g3_19', name: '综合评价校测', event_date: d3(6, 27), category: 'comprehensive_eval', type: 'system' },
  { id: 'g3_20', name: '志愿填报', event_date: d3(7, 1), category: 'volunteer_fill', type: 'system' },
  { id: 'g3_21', name: '录取结果（综评批）', event_date: d3(7, 8), category: 'result_release', type: 'system' },
  { id: 'g3_22', name: '录取结果（本科普通批）', event_date: d3(7, 15), category: 'result_release', type: 'system' }
];

var GAO2_MILESTONES = [
  { id: 'g2_01', name: '高二选科确认', event_date: d(10, 1), category: 'registration', type: 'system' },
  { id: 'g2_02', name: '期中考试（上学期）', event_date: d(11, 10), category: 'school_exam', type: 'system' },
  { id: 'g2_03', name: '合格考（1月）', event_date: d(1, 3), category: 'qualification_exam', type: 'system' },
  { id: 'g2_04', name: '期末考试（上学期）', event_date: d(1, 15), category: 'school_exam', type: 'system' },
  { id: 'g2_05', name: '期中考试（下学期）', event_date: d(4, 10), category: 'school_exam', type: 'system' },
  { id: 'g2_06', name: '合格考（6月）', event_date: d(6, 20), category: 'qualification_exam', type: 'system' },
  { id: 'g2_07', name: '期末考试（下学期）', event_date: d(6, 25), category: 'school_exam', type: 'system' }
];

var GAO1_MILESTONES = [
  { id: 'g1_01', name: '开学（上学期）', event_date: d(9, 1), category: 'semester', type: 'system' },
  { id: 'g1_02', name: '月考（9月）', event_date: d(9, 25), category: 'school_exam', type: 'system' },
  { id: 'g1_03', name: '家长会', event_date: d(10, 15), category: 'parent_meeting', type: 'system' },
  { id: 'g1_04', name: '月考（10月）', event_date: d(10, 25), category: 'school_exam', type: 'system' },
  { id: 'g1_05', name: '期中考试（上学期）', event_date: d(11, 10), category: 'school_exam', type: 'system' },
  { id: 'g1_06', name: '合格考', event_date: d(11, 20), category: 'qualification_exam', type: 'system' },
  { id: 'g1_07', name: '期末考试（上学期）', event_date: d(1, 15), category: 'school_exam', type: 'system' },
  { id: 'g1_08', name: '期中考试（下学期）', event_date: d(4, 10), category: 'school_exam', type: 'system' },
  { id: 'g1_09', name: '合格考（6月）', event_date: d(6, 20), category: 'qualification_exam', type: 'system' },
  { id: 'g1_10', name: '期末考试（下学期）', event_date: d(6, 25), category: 'school_exam', type: 'system' }
];

module.exports = {
  getMilestones: function(grade) {
    if (grade === 'gao3') return GAO3_MILESTONES;
    if (grade === 'gao2') return GAO2_MILESTONES;
    if (grade === 'gao1') return GAO1_MILESTONES;
    return GAO3_MILESTONES;
  }
};
