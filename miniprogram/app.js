App({
  globalData: {
    userInfo: null,
    token: null,
    currentStudent: null,
    baseUrl: 'http://localhost:8000'  // Change in production
  },

  onLaunch() {
    // Check login status
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
      // Load current student
      const currentStudent = wx.getStorageSync('currentStudent');
      if (currentStudent) {
        this.globalData.currentStudent = currentStudent;
      }
    }
  },

  // Helper: check if user is logged in
  isLoggedIn() {
    return !!this.globalData.token;
  },

  // Helper: get current student ID
  getCurrentStudentId() {
    return this.globalData.currentStudent?.id || null;
  }
});
