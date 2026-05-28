var api = require('./api');

function listGrowthRecords(studentId, params) {
  return api.get('/api/students/' + studentId + '/growth-records', params);
}

function createGrowthRecord(studentId, data) {
  return api.post('/api/students/' + studentId + '/growth-records', data);
}

function deleteGrowthRecord(studentId, recordId) {
  return api.del('/api/students/' + studentId + '/growth-records/' + recordId);
}

module.exports = {
  listGrowthRecords: listGrowthRecords,
  createGrowthRecord: createGrowthRecord,
  deleteGrowthRecord: deleteGrowthRecord
};
