/**
 * Core API request module.
 * Handles: base URL, JWT token injection, error handling, token refresh.
 */

const app = getApp();

/**
 * Get the base URL (lazily, since getApp() may not be ready at module load time).
 */
function getBaseUrl() {
  return (app && app.globalData && app.globalData.baseUrl) || 'http://localhost:8000';
}

/**
 * Send an HTTP request to the backend API.
 * @param {Object} options
 * @param {string} options.url - API path (e.g., '/api/students')
 * @param {string} [options.method='GET'] - HTTP method
 * @param {Object} [options.data] - Request body
 * @param {Object} [options.header] - Additional headers
 * @param {boolean} [options.auth=true] - Whether to include auth token
 * @param {boolean} [options.showError=true] - Whether to show error toast
 * @returns {Promise<Object>} Response data
 */
function request(options) {
  const {
    url,
    method = 'GET',
    data = {},
    header = {},
    auth = true,
    showError = true
  } = options;

  return new Promise((resolve, reject) => {
    // Build full URL
    const fullUrl = url.startsWith('http') ? url : getBaseUrl() + url;

    // Build headers
    const headers = {
      'Content-Type': 'application/json',
      ...header
    };

    // Add Authorization header if auth=true and token exists
    if (auth && app && app.globalData && app.globalData.token) {
      headers['Authorization'] = 'Bearer ' + app.globalData.token;
    }

    wx.request({
      url: fullUrl,
      method: method,
      data: data,
      header: headers,
      success(res) {
        const statusCode = res.statusCode;

        // 2xx — success
        if (statusCode >= 200 && statusCode < 300) {
          resolve(res.data);
          return;
        }

        // 401 — Unauthorized: clear token, redirect to login
        if (statusCode === 401) {
          if (app && app.globalData) {
            app.globalData.token = null;
            app.globalData.currentStudent = null;
          }
          wx.removeStorageSync('token');
          wx.removeStorageSync('currentStudent');

          if (showError) {
            wx.showToast({
              title: '登录已过期，请重新登录',
              icon: 'none',
              duration: 2000
            });
          }

          // Navigate to index after a short delay
          setTimeout(() => {
            wx.reLaunch({ url: '/pages/index/index' });
          }, 1500);

          reject({ code: 401, message: '登录已过期' });
          return;
        }

        // 403 — Forbidden: check for free-limit errors
        if (statusCode === 403) {
          const errorCode = res.data && res.data.error_code;
          if (errorCode && errorCode.startsWith && errorCode.startsWith('FREE_LIMIT_')) {
            // Show upgrade modal
            wx.showModal({
              title: '功能受限',
              content: res.data.message || '免费版已达使用上限，升级标准版解锁更多功能',
              confirmText: '去升级',
              cancelText: '知道了',
              success(modalRes) {
                if (modalRes.confirm) {
                  wx.navigateTo({ url: '/pages/profile/subscription' });
                }
              }
            });
          } else if (showError) {
            wx.showToast({
              title: res.data.message || '没有权限',
              icon: 'none',
              duration: 2000
            });
          }

          reject({ code: 403, message: res.data.message || '没有权限', data: res.data });
          return;
        }

        // Other errors
        if (showError) {
          wx.showToast({
            title: res.data.message || '请求失败',
            icon: 'none',
            duration: 2000
          });
        }

        reject({
          code: statusCode,
          message: res.data.message || '请求失败',
          data: res.data
        });
      },
      fail(err) {
        // Network error
        if (showError) {
          wx.showToast({
            title: '网络不给力，请检查网络后重试',
            icon: 'none',
            duration: 2000
          });
        }

        reject({
          code: -1,
          message: '网络错误',
          detail: err
        });
      }
    });
  });
}

/**
 * GET request convenience method.
 */
function get(url, data, options) {
  return request({
    url: url,
    method: 'GET',
    data: data,
    ...options
  });
}

/**
 * POST request convenience method.
 */
function post(url, data, options) {
  return request({
    url: url,
    method: 'POST',
    data: data,
    ...options
  });
}

/**
 * PUT request convenience method.
 */
function put(url, data, options) {
  return request({
    url: url,
    method: 'PUT',
    data: data,
    ...options
  });
}

/**
 * DELETE request convenience method.
 */
function del(url, data, options) {
  return request({
    url: url,
    method: 'DELETE',
    data: data,
    ...options
  });
}

/**
 * Upload a file (image) to the backend.
 * @param {string} filePath - Local file path from wx.chooseImage
 * @param {Object} [options] - Additional options
 * @param {string} [options.name='file'] - Form field name
 * @param {Object} [options.formData] - Additional form data
 * @param {boolean} [options.showError=true] - Whether to show error toast
 * @returns {Promise<Object>} Upload response data
 */
function uploadFile(filePath, options = {}) {
  const {
    name = 'file',
    formData = {},
    showError = true
  } = options;

  return new Promise((resolve, reject) => {
    const headers = {};
    if (app && app.globalData && app.globalData.token) {
      headers['Authorization'] = 'Bearer ' + app.globalData.token;
    }

    wx.uploadFile({
      url: getBaseUrl() + '/api/upload/image',
      filePath: filePath,
      name: name,
      header: headers,
      formData: formData,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          // wx.uploadFile returns data as string, parse it
          let data;
          try {
            data = JSON.parse(res.data);
          } catch (e) {
            data = res.data;
          }
          resolve(data);
        } else {
          let errData;
          try {
            errData = JSON.parse(res.data);
          } catch (e) {
            errData = { message: '上传失败' };
          }

          if (showError) {
            wx.showToast({
              title: errData.message || '上传失败',
              icon: 'none',
              duration: 2000
            });
          }

          reject({
            code: res.statusCode,
            message: errData.message || '上传失败',
            data: errData
          });
        }
      },
      fail(err) {
        if (showError) {
          wx.showToast({
            title: '网络不给力，上传失败',
            icon: 'none',
            duration: 2000
          });
        }

        reject({
          code: -1,
          message: '网络错误',
          detail: err
        });
      }
    });
  });
}

module.exports = { request, get, post, put, del, uploadFile };
