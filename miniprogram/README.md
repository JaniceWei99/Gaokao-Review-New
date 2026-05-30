# 微信小程序前端

## 环境要求

1. **微信开发者工具**（WeChat Developer Tools）
   - 下载地址：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html

2. **微信账号**（用于小程序注册和测试）

## 项目结构

```
miniprogram/
├── app.js              # 小程序入口，初始化全局数据
├── app.json            # 全局配置（页面路径、窗口样式、tabBar等）
├── app.wxss            # 全局样式表
├── project.config.json # 项目配置文件
├── project.private.config.json # 本地项目配置
├── pages/              # 34个页面（136+文件）
│   ├── onboarding/     # 6页：欢迎、年级选择、选科、1月英语、区县选择、完成
│   ├── index/          # 首页（倒计时+金句+里程碑摘要+功能入口）
│   ├── milestones/     # 3页：时间线、行动卡片、自定义里程碑
│   ├── exams/          # 3页：考试列表、添加、趋势
│   ├── errors/         # 3页：错题列表、添加、详情
│   ├── growth/         # 3页：成长记录时间线、添加、导出
│   ├── quotes/         # 1页：金句收藏
│   ├── knowledge/      # 1页：知识树浏览
│   ├── school-progress/ # 1页：学校复习进度
│   ├── ai/             # 4页：AI聊天、聊天历史、月度报告、建议
│   └── profile/        # 6页：个人中心、学生管理、订阅、隐私、关于、账号切换
├── services/           # 9个服务模块
│   ├── api.js          # HTTP请求封装（BASE_URL配置）
│   ├── auth.js         # 微信登录认证
│   ├── account.js      # 本地账号CRUD、密码哈希、账号切换
│   ├── student.js      # 学生档案管理
│   ├── storage.js      # 本地存储封装
│   ├── sync.js         # 数据同步
│   ├── upload.js       # 图片上传
│   ├── errorNote.js    # 错题本服务
│   └── growth.js       # 成长记录服务
├── utils/              # 工具函数
│   ├── date.js         # 日期处理
│   └── storage.js      # 本地存储封装
└── constants/          # 常量定义
    ├── subjects.js     # 科目定义
    ├── districts.js    # 上海16个区
    └── plans.js        # 订阅计划
```

## 在微信开发者工具中打开项目

### 步骤1：安装微信开发者工具

下载并安装微信开发者工具：
https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html

### 步骤2：打开项目

1. 启动微信开发者工具
2. 选择"小程序"项目类型
3. 点击"导入项目"
4. 选择项目目录：`/Users/janicewei/Documents/trae_projects/Gaokao-Mini/Gaokao-Review-New/miniprogram`
5. 填写AppID：
   - 测试阶段：选择"测试号"或使用自己的小程序AppID
   - 正式上线：需要在微信公众平台注册小程序
6. 点击"导入"

### 步骤3：配置后端API地址

由于后端运行在本地（localhost:8000），需要在微信开发者工具中：

1. 点击右上角"详情"
2. 选择"本地设置"
3. 勾选"不校验合法域名、web-view（业务域名）、TLS版本以及HTTPS证书"
4. 或修改 `services/api.js` 中的 `BASE_URL` 为实际后端地址

### 步骤4：编译和预览

微信开发者工具会自动编译项目：
- **编译**：Ctrl+B 或点击"编译"按钮
- **预览**：生成二维码，手机扫码预览
- **真机调试**：连接手机，实时调试

## 服务模块说明

| 服务 | 文件 | 说明 |
|------|------|------|
| API | `services/api.js` | HTTP请求封装，统一错误处理，Token注入 |
| Auth | `services/auth.js` | 微信登录、Token管理、认证状态 |
| Account | `services/account.js` | 本地账号CRUD、密码哈希、账号切换、数据命名空间 |
| Student | `services/student.js` | 学生档案CRUD、Onboarding |
| Storage | `services/storage.js` | 本地存储封装 |
| Sync | `services/sync.js` | 本地<->服务端数据同步 |
| Upload | `services/upload.js` | 图片压缩上传 |
| ErrorNote | `services/errorNote.js` | 错题本服务 |
| Growth | `services/growth.js` | 成长记录服务 |

## 功能状态

### Phase 1 — 核心MVP ✅

| 功能 | 状态 | 页面 |
|------|------|------|
| Onboarding流程 | ✅ | 6个页面（欢迎→年级→选科→英语→区县→完成） |
| 首页Dashboard | ✅ | 倒计时、金句、里程碑摘要、功能入口 |
| 里程碑时间线 | ✅ | 系统里程碑+自定义，按年级/选科/区筛选 |
| 行动卡片 | ✅ | 里程碑前15天/3天行动建议 |
| 每日金句 | ✅ | 60条金句，8个分类，每日分配 |
| 知识点树 | ✅ | 2级展开，365个知识点 |
| 成绩录入 | ✅ | 最多3次考试（免费版），自定义满分 |
| 成绩趋势 | ✅ | 各科得分率趋势图 |
| 个人中心 | ✅ | 学生管理、隐私政策、关于 |
| 多孩切换 | ✅ | 账号切换组件 |

### Phase 1.5 — 错题本 + 成长记录 ✅

| 功能 | 状态 | 页面 |
|------|------|------|
| 错题拍照录入 | ✅ | 3步流程：拍照→选科目/知识点→标注→保存 |
| 错题列表 | ✅ | 筛选器+卡片列表+统计摘要 |
| 错题详情 | ✅ | 图片查看+元数据编辑+删除 |
| 成长记录时间线 | ✅ | 按学年分组，5种类型图标 |
| 添加成长记录 | ✅ | 5种类型切换+奖项详情+拍照上传 |
| 成长档案导出 | ✅ | 长图/PDF导出 |

### Phase 2 — 付费功能 (前端就绪)

| 功能 | 状态 | 页面 |
|------|------|------|
| 订阅管理 | ✅ | 免费/标准/高级套餐展示，支付流程 |
| 学校进度记录 | ✅ | 复习进度列表 |

### Phase 3 — AI功能 (前端就绪)

| 功能 | 状态 | 页面 |
|------|------|------|
| AI聊天 | ✅ | 对话界面，上下文管理 |
| 聊天历史 | ✅ | 历史会话列表 |
| 月度报告 | ✅ | AI生成的月度成长报告展示 |
| AI建议 | ✅ | 个性化行动建议展示 |

## 调试技巧

### 1. 控制台调试
- 微信开发者工具底部有"Console"面板
- 使用 `console.log()` 输出调试信息
- 支持断点调试

### 2. 网络请求调试
- "Network"面板查看所有网络请求
- 查看请求/响应详情
- 支持模拟网络环境

### 3. 数据存储调试
- "Storage"面板查看本地存储数据
- 可以手动添加/修改/删除存储数据

### 4. 页面调试
- "Wxml"面板查看页面结构
- "WXSS"面板查看样式
- 支持实时修改预览

## 常见问题

### Q1: 后端API请求失败
**原因**：微信小程序要求使用HTTPS，且域名需要在小程序后台配置

**解决方案**：
- 开发阶段：在"本地设置"中关闭域名校验
- 生产环境：配置HTTPS域名并在小程序后台添加

### Q2: 无法登录
**原因**：后端未配置微信AppID和AppSecret

**解决方案**：
- 在 `server/.env` 中配置 `WX_APP_ID` 和 `WX_APP_SECRET`
- 或使用测试号进行开发

### Q3: 页面白屏
**原因**：JS代码有语法错误或逻辑错误

**解决方案**：
- 查看Console面板的错误信息
- 检查 `app.js` 和页面 `js` 文件的逻辑

### Q4: 样式不生效
**原因**：WXSS选择器问题或样式优先级

**解决方案**：
- 检查"WXSS"面板
- 使用 `!important` 提高优先级
- 检查是否使用了不支持的CSS属性

## 相关文档

- 微信小程序官方文档：https://developers.weixin.qq.com/miniprogram/dev/framework/
- 组件文档：https://developers.weixin.qq.com/miniprogram/dev/component/
- API文档：https://developers.weixin.qq.com/miniprogram/dev/api/
