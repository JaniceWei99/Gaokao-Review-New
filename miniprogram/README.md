# 微信小程序开发指南

## 环境要求

1. **微信开发者工具**（WeChat Developer Tools）
   - 下载地址：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html
   - Windows/Mac/Linux版本

2. **微信账号**（用于小程序注册和测试）

3. **Node.js**（可选，用于代码语法检查）
   - 项目已验证所有JS文件语法正确

## 项目结构验证

当前小程序项目结构完整：
- ✅ 29个JSON文件（全部有效）
- ✅ 34个JavaScript文件（全部语法正确）
- ✅ 26个页面（每个页面包含.js/.json/.wxml/.wxss）
- ✅ app.js/app.json/app.wxss（入口文件）
- ✅ project.config.json（项目配置）
- ✅ services/（API服务层）
- ✅ utils/（工具函数）
- ✅ constants/（常量定义）

## 在微信开发者工具中打开项目

### 步骤1：安装微信开发者工具

下载并安装微信开发者工具：
- Windows: https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html
- Mac: 同上

### 步骤2：打开项目

1. 启动微信开发者工具
2. 选择"小程序"项目类型
3. 点击"导入项目"
4. 选择项目目录：`/home/mystic/my_projects/Gaokao-review-new/miniprogram`
   - 在Windows上：`C:\Users\YourName\Gaokao-Review-New\miniprogram`
5. 填写AppID：
   - 测试阶段：选择"测试号"或使用自己的小程序AppID
   - 正式上线：需要在微信公众平台注册小程序
6. 点击"导入"

### 步骤3：配置后端API地址

由于当前后端运行在本地（localhost:8000），需要在微信开发者工具中：

1. 点击右上角"详情"
2. 选择"本地设置"
3. 勾选"不校验合法域名、web-view（业务域名）、TLS版本以及HTTPS证书"
4. 或者修改`miniprogram/services/api.js`中的`BASE_URL`为实际的后端地址

### 步骤4：编译和预览

微信开发者工具会自动编译项目：
- **编译**：Ctrl+B 或 点击"编译"按钮
- **预览**：生成二维码，手机扫码预览
- **真机调试**：连接手机，实时调试

## 小程序文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| app.js | 小程序入口，初始化全局数据 |
| app.json | 全局配置（页面路径、窗口样式、tabBar等） |
| app.wxss | 全局样式表 |
| project.config.json | 项目配置文件 |

### 页面结构

每个页面包含4个文件：
- `pages/xxx/xxx.js` - 页面逻辑
- `pages/xxx/xxx.json` - 页面配置
- `pages/xxx/xxx.wxml` - 页面结构（类似HTML）
- `pages/xxx/xxx.wxss` - 页面样式（类似CSS）

### 服务层

- `services/api.js` - HTTP请求封装
- `services/auth.js` - 微信登录认证

### 工具函数

- `utils/date.js` - 日期处理
- `utils/storage.js` - 本地存储封装

### 常量定义

- `constants/subjects.js` - 科目定义
- `constants/districts.js` - 上海16个区
- `constants/plans.js` - 订阅计划

## 当前功能状态

### 已实现（骨架）

所有26个页面的基础结构已创建：
- ✅ onboarding（欢迎、年级选择、选科、1月英语、区县选择、完成）
- ✅ index（首页）
- ✅ milestones（时间线、行动卡片、自定义里程碑）
- ✅ knowledge（知识树浏览）
- ✅ exams（考试列表、添加、趋势）
- ✅ errors（错题列表、添加、详情）
- ✅ growth（成长记录时间线、添加、导出）
- ✅ quotes（收藏）
- ✅ profile（个人中心、学生管理、订阅、隐私、关于）

### 待实现（Phase 1+）

页面逻辑和API调用将在Phase 1开发时完善：
- WeChat登录集成
- 学生档案CRUD
- 里程碑显示和提醒
- 每日金句显示
- Dashboard数据聚合

## 调试技巧

### 1. 控制台调试

- 微信开发者工具底部有"Console"面板
- 可以使用`console.log()`输出调试信息
- 支持断点调试

### 2. 网络请求调试

- "Network"面板可以查看所有网络请求
- 可以查看请求/响应详情
- 支持模拟网络环境

### 3. 数据存储调试

- "Storage"面板可以查看本地存储数据
- 可以手动添加/修改/删除存储数据

### 4. 页面调试

- "Wxml"面板可以查看页面结构
- "WXSS"面板可以查看样式
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
- 在`server/.env`中配置`WX_APP_ID`和`WX_APP_SECRET`
- 或使用测试号进行开发

### Q3: 页面白屏

**原因**：JS代码有语法错误或逻辑错误

**解决方案**：
- 查看Console面板的错误信息
- 检查`app.js`和页面`js`文件的逻辑

### Q4: 样式不生效

**原因**：WXSS选择器问题或样式优先级

**解决方案**：
- 检查"WXSS"面板
- 使用`!important`提高优先级
- 检查是否使用了不支持的CSS属性

## 命令行编译（可选）

微信开发者工具提供CLI接口，可以在命令行中执行：

```bash
# Windows路径示例
"C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat"

# 常用命令
# 自动预览
cli auto-preview --project /path/to/miniprogram

# 上传代码
cli upload --project /path/to/miniprogram --version 1.0.0 --desc "描述"
```

详细文档：https://developers.weixin.qq.com/miniprogram/dev/devtools/cli.html

## 下一步

1. 在Windows上安装微信开发者工具
2. 打开`miniprogram`目录
3. 编译并预览项目结构
4. 等待Phase 1开发完成后，连接后端API进行完整测试

## 相关文档

- 微信小程序官方文档：https://developers.weixin.qq.com/miniprogram/dev/framework/
- 组件文档：https://developers.weixin.qq.com/miniprogram/dev/component/
- API文档：https://developers.weixin.qq.com/miniprogram/dev/api/
