/**
 * Region data — keyed by province for multi-province support.
 * For Phase 1, only Shanghai regions are included.
 */

var PROVINCES = {
  shanghai: { id: 'shanghai', name: '上海' }
};

var ALL_REGIONS = [
  { id: 'huangpu', name: '黄浦区', province: 'shanghai' },
  { id: 'xuhui', name: '徐汇区', province: 'shanghai' },
  { id: 'changning', name: '长宁区', province: 'shanghai' },
  { id: 'jingan', name: '静安区', province: 'shanghai' },
  { id: 'putuo', name: '普陀区', province: 'shanghai' },
  { id: 'hongkou', name: '虹口区', province: 'shanghai' },
  { id: 'yangpu', name: '杨浦区', province: 'shanghai' },
  { id: 'minhang', name: '闵行区', province: 'shanghai' },
  { id: 'baoshan', name: '宝山区', province: 'shanghai' },
  { id: 'jiading', name: '嘉定区', province: 'shanghai' },
  { id: 'pudong', name: '浦东新区', province: 'shanghai' },
  { id: 'jinshan', name: '金山区', province: 'shanghai' },
  { id: 'songjiang', name: '松江区', province: 'shanghai' },
  { id: 'qingpu', name: '青浦区', province: 'shanghai' },
  { id: 'fengxian', name: '奉贤区', province: 'shanghai' },
  { id: 'chongming', name: '崇明区', province: 'shanghai' }
];

function getRegions(province) {
  if (!province) { province = 'shanghai'; }
  return ALL_REGIONS.filter(function(r) { return r.province === province; });
}

module.exports = {
  PROVINCES: PROVINCES,
  ALL_REGIONS: ALL_REGIONS,
  getRegions: getRegions,
  DISTRICTS: ALL_REGIONS
};
