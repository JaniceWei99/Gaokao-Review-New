var api = require('../../services/api');
var permission = require('../../utils/permission');
var app = getApp();

Page({
  data: {
    subjectId: '',
    subjectOptions: [
      { key: 'chinese', label: '语文' },
      { key: 'math', label: '数学' },
      { key: 'english', label: '英语' },
      { key: 'physics', label: '物理' },
      { key: 'chemistry', label: '化学' },
      { key: 'biology', label: '生物' },
      { key: 'politics', label: '政治' },
      { key: 'history', label: '历史' },
      { key: 'geography', label: '地理' }
    ],
    subjectIndex: -1,
    tree: [],
    loading: false,
    expandedNodes: {},
    canExpandL3: false
  },

  onLoad: function() {
    var sub = app.globalData.subscription;
    this.setData({
      canExpandL3: permission.canUse('knowledge_l3', sub)
    });
  },

  onShow: function() {
    var sub = app.globalData.subscription;
    this.setData({
      canExpandL3: permission.canUse('knowledge_l3', sub)
    });
  },

  onSubjectChange: function(e) {
    var idx = parseInt(e.detail.value);
    var subjectId = this.data.subjectOptions[idx].key;
    this.setData({
      subjectIndex: idx,
      subjectId: subjectId,
      tree: [],
      expandedNodes: {}
    });
    this.loadTree(subjectId);
  },

  loadTree: function(subjectId) {
    var that = this;
    var studentId = app.getCurrentStudentId();
    if (!studentId || !subjectId) return;

    that.setData({ loading: true });

    api.get('/api/knowledge', {
      subject_id: subjectId,
      student_id: studentId,
      max_level: 2
    }).then(function(res) {
      that.setData({
        tree: res || [],
        loading: false
      });
    }).catch(function(err) {
      console.warn('[Knowledge] load error:', err);
      that.setData({ loading: false });
    });
  },

  onToggleNode: function(e) {
    var id = e.currentTarget.dataset.id;
    var level = e.currentTarget.dataset.level;
    var expanded = JSON.parse(JSON.stringify(this.data.expandedNodes));

    if (expanded[id]) {
      delete expanded[id];
    } else {
      if (level === 2 && !this.data.canExpandL3) {
        permission.showUpgradeModal('FEATURE_REQUIRES_STANDARD');
        return;
      }
      expanded[id] = true;
      if (level === 2) {
        this.loadLevel3(id);
      }
    }

    this.setData({ expandedNodes: expanded });
  },

  loadLevel3: function(parentId) {
    var that = this;
    api.get('/api/knowledge/level3/' + parentId).then(function(res) {
      var tree = JSON.parse(JSON.stringify(that.data.tree));
      that.attachLevel3(tree, parentId, res || []);
      that.setData({ tree: tree });
    }).catch(function(err) {
      if (err && err.code === 'FEATURE_REQUIRES_STANDARD') {
        permission.showUpgradeModal('FEATURE_REQUIRES_STANDARD');
      }
    });
  },

  attachLevel3: function(nodes, parentId, level3Nodes) {
    for (var i = 0; i < nodes.length; i++) {
      if (nodes[i].id === parentId) {
        nodes[i].children = level3Nodes;
        return true;
      }
      if (nodes[i].children && nodes[i].children.length > 0) {
        if (this.attachLevel3(nodes[i].children, parentId, level3Nodes)) {
          return true;
        }
      }
    }
    return false;
  },

  onUpgrade: function() {
    wx.navigateTo({ url: '/pages/profile/subscription' });
  }
});
