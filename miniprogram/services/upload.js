var api = require('./api');

function requestUploadCredential(prefix, studentId, extension) {
  return api.post('/api/upload/image', {
    prefix: prefix || 'errors',
    student_id: studentId,
    extension: extension || 'jpg'
  });
}

function uploadImageToCOS(filePath, credentials) {
  return new Promise(function(resolve, reject) {
    wx.uploadFile({
      url: credentials.upload_url,
      filePath: filePath,
      name: 'file',
      formData: {
        key: credentials.image_key,
        'x-cos-security-token': credentials.tmp_secret_token || ''
      },
      success: function(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ image_key: credentials.image_key });
        } else {
          reject(new Error('Upload failed: ' + res.statusCode));
        }
      },
      fail: function(err) {
        reject(err);
      }
    });
  });
}

module.exports = {
  requestUploadCredential: requestUploadCredential,
  uploadImageToCOS: uploadImageToCOS
};
