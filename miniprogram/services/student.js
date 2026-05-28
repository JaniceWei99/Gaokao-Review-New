var api = require('./api');

function createStudent(data) {
  return api.post('/api/students', data);
}

function getStudent(studentId) {
  return api.get('/api/students/' + studentId);
}

function updateStudent(studentId, data) {
  return api.put('/api/students/' + studentId, data);
}

function listStudents() {
  return api.get('/api/students');
}

function deleteStudent(studentId) {
  return api.del('/api/students/' + studentId);
}

function getDashboard(studentId) {
  return api.get('/api/students/' + studentId + '/dashboard');
}

module.exports = {
  createStudent: createStudent,
  getStudent: getStudent,
  updateStudent: updateStudent,
  listStudents: listStudents,
  deleteStudent: deleteStudent,
  getDashboard: getDashboard
};
