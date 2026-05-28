var api = require('./api');

function listErrorNotes(studentId, params) {
  return api.get('/api/students/' + studentId + '/error-notes', params);
}

function getErrorNote(studentId, noteId) {
  return api.get('/api/students/' + studentId + '/error-notes/' + noteId);
}

function createErrorNote(studentId, data) {
  return api.post('/api/students/' + studentId + '/error-notes', data);
}

function deleteErrorNote(studentId, noteId) {
  return api.del('/api/students/' + studentId + '/error-notes/' + noteId);
}

function getErrorNoteStats(studentId) {
  return api.get('/api/students/' + studentId + '/error-notes/stats');
}

module.exports = {
  listErrorNotes: listErrorNotes,
  getErrorNote: getErrorNote,
  createErrorNote: createErrorNote,
  deleteErrorNote: deleteErrorNote,
  getErrorNoteStats: getErrorNoteStats
};
