/**
 * Auth service — handles WeChat login, onboarding check, and logout.
 */

const api = require('./api');

module.exports = {
  /**
   * WeChat login flow.
   * 1. Calls wx.login() to get a temporary code
   * 2. Sends code to backend POST /api/auth/wx-login
   * 3. Stores token and user info in globalData and local storage
   * @returns {Promise<{token: string, user: Object, is_new_user: boolean}>}
   */
  async wxLogin() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: async (loginRes) => {
          if (!loginRes.code) {
            wx.showToast({
              title: '微信登录失败，请重试',
              icon: 'none'
            });
            reject(new Error('wx.login failed: no code'));
            return;
          }

          try {
            // Send code to backend
            const result = await api.post('/api/auth/wx-login', {
              code: loginRes.code
            }, { auth: false });

            const app = getApp();

            // Store token
            if (result.token) {
              app.globalData.token = result.token;
              wx.setStorageSync('token', result.token);
            }

            // Store user info
            if (result.user) {
              app.globalData.userInfo = result.user;
              wx.setStorageSync('userInfo', result.user);
            }

            resolve({
              token: result.token,
              user: result.user,
              is_new_user: !!result.is_new_user
            });
          } catch (err) {
            reject(err);
          }
        },
        fail: (err) => {
          wx.showToast({
            title: '微信登录失败，请重试',
            icon: 'none'
          });
          reject(err);
        }
      });
    });
  },

  /**
   * Check if user needs onboarding (i.e., has no students configured).
   * @returns {Promise<boolean>} true if onboarding is needed
   */
  async checkOnboarding() {
    try {
      const result = await api.get('/api/students');
      const students = result.data || result;
      // If no students, user needs onboarding
      return !students || (Array.isArray(students) && students.length === 0);
    } catch (err) {
      // If error (e.g., 401), assume onboarding needed
      return true;
    }
  },

  /**
   * Logout — clears token and all user data from storage and globalData.
   */
  logout() {
    const app = getApp();
    app.globalData.token = null;
    app.globalData.userInfo = null;
    app.globalData.currentStudent = null;

    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    wx.removeStorageSync('currentStudent');

    // Navigate to index
    wx.reLaunch({ url: '/pages/index/index' });
  }
};
