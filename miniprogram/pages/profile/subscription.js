var api = require('../../services/api');
var app = getApp();

Page({
  data: {
    subscription: null,
    loading: true,
    plans: [
      {
        key: 'free',
        name: '免费版',
        price: '¥0',
        desc: '基础功能体验',
        features: [
          '里程碑时间线',
          '每日金句',
          '错题本(限10道)',
          '成长记录(限5条)',
          '成绩录入(限3次)'
        ],
        current: false
      },
      {
        key: 'standard',
        name: '标准版',
        price: '¥19.9/月',
        desc: '最受欢迎',
        popular: true,
        billingOptions: [
          { key: 'monthly', label: '月付', price: 19.9, display: '¥19.9/月' },
          { key: 'yearly', label: '年付', price: 199, display: '¥199/年', save: '省¥39.8' },
          { key: 'lifetime_high_school', label: '全程包', price: 399, display: '¥399/高中全程', save: '最划算' }
        ],
        selectedBilling: 'yearly',
        features: [
          '里程碑行动卡片',
          '完整金句库300+条',
          '金句收藏与分享',
          '知识点三级展开',
          '无限错题存储',
          '无限成长记录',
          '成绩趋势分析',
          '成长档案导出'
        ],
        current: false
      },
      {
        key: 'premium',
        name: '高级版',
        price: '¥39.9/月',
        desc: 'AI智能陪伴',
        billingOptions: [
          { key: 'monthly', label: '月付', price: 39.9, display: '¥39.9/月' },
          { key: 'yearly', label: '年付', price: 399, display: '¥399/年', save: '省¥79.8' },
          { key: 'lifetime_high_school', label: '全程包', price: 799, display: '¥799/高中全程', save: '最划算' }
        ],
        selectedBilling: 'yearly',
        features: [
          '标准版全部功能',
          'AI家长顾问对话',
          'AI个性化行动建议',
          'AI个性化金句',
          'AI错题分类助手',
          'AI月度成长报告',
          '高级版专属客服'
        ],
        current: false
      }
    ],
    purchasing: false
  },

  onLoad: function() {
    this.loadSubscription();
  },

  onShow: function() {
    this.loadSubscription();
  },

  loadSubscription: function() {
    var that = this;
    api.get('/api/subscription').then(function(res) {
      var sub = res;
      var plans = that.data.plans.map(function(p) {
        p.current = p.key === sub.plan;
        return p;
      });

      that.setData({
        subscription: sub,
        plans: plans,
        loading: false
      });
    }).catch(function() {
      that.setData({ loading: false });
    });
  },

  onBillingChange: function(e) {
    var planIndex = e.currentTarget.dataset.plan;
    var billingKey = e.currentTarget.dataset.billing;
    var plans = this.data.plans;
    plans[planIndex].selectedBilling = billingKey;
    this.setData({ plans: plans });
  },

  onUpgrade: function(e) {
    var that = this;
    var planKey = e.currentTarget.dataset.plan;
    if (planKey === 'free') return;

    var plan = this.data.plans.find(function(p) { return p.key === planKey; });
    if (!plan) return;

    var billingType = plan.selectedBilling || 'yearly';
    var billingOption = plan.billingOptions.find(function(b) { return b.key === billingType; });

    var priceDisplay = billingOption ? billingOption.display : plan.price;

    wx.showModal({
      title: '确认订阅',
      content: '确认订阅' + plan.name + '（' + priceDisplay + '）？',
      confirmText: '确认支付',
      success: function(res) {
        if (res.confirm) {
          that.doUpgrade(planKey, billingType);
        }
      }
    });
  },

  doUpgrade: function(plan, billingType) {
    var that = this;
    that.setData({ purchasing: true });

    api.post('/api/subscription/upgrade', {
      plan: plan,
      billing_type: billingType
    }).then(function(res) {
      that.setData({ purchasing: false });

      if (res.package && res.package.indexOf('mock_prepay_id') >= 0) {
        wx.showToast({ title: '模拟支付成功', icon: 'success' });
        setTimeout(function() {
          that.loadSubscription();
        }, 1500);
        return;
      }

      wx.requestPayment({
        timeStamp: res.timeStamp,
        nonceStr: res.nonceStr,
        package: res.package,
        signType: res.signType,
        paySign: res.paySign,
        success: function() {
          wx.showToast({ title: '订阅成功！', icon: 'success' });
          setTimeout(function() {
            that.loadSubscription();
          }, 1500);
        },
        fail: function(err) {
          if (err.errMsg && err.errMsg.indexOf('cancel') >= 0) {
            wx.showToast({ title: '已取消支付', icon: 'none' });
          } else {
            wx.showToast({ title: '支付失败，请重试', icon: 'none' });
          }
        }
      });
    }).catch(function() {
      that.setData({ purchasing: false });
      wx.showToast({ title: '操作失败，请重试', icon: 'none' });
    });
  },

  onStartTrial: function() {
    var that = this;
    api.post('/api/subscription/start-trial').then(function() {
      wx.showToast({ title: '试用已开启！', icon: 'success' });
      setTimeout(function() {
        that.loadSubscription();
      }, 1500);
    }).catch(function() {
      wx.showToast({ title: '操作失败', icon: 'none' });
    });
  }
});
