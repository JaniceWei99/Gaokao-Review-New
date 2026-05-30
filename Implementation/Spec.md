

好的，我根据 Product Vision v5.1 的完整内容，按照规范驱动开发（SDD）的最佳实践，生成一份可直接用于 AI 编程助手（如 Cursor、Claude Code、GitHub Copilot 等）生成代码的 `spec.md`。

---

```markdown
# spec.md — 上海高考复习助手 v5.1

## 项目概述

### 项目名称
高考家长帮（Gaokao Parent Companion）

### 一句话描述
一款面向上海高中生家长的微信小程序，通过里程碑驱动的行动提醒、每日励志金句、错题拍照归档和孩子成长记录，帮助家长在高考备考全程中不焦虑、不缺席、不越界。

### 目标用户
上海高一至高三考生家长（40-50岁），熟练使用微信但不擅长复杂App。产品为**纯家长端工具**，孩子无需任何操作。

### 技术栈
- **前端**: 微信小程序（WXML + WXSS + JavaScript/TypeScript）
- **后端**: Node.js（或 Python FastAPI），RESTful API
- **数据库**: MySQL（或 PostgreSQL）用于结构化数据；对象存储（如腾讯云 COS）用于图片
- **部署**: 腾讯云（与微信生态集成最优）
- **认证**: 微信登录（wx.login）

### 合规红线（开发过程中必须遵守）
- ❌ 不得提供任何学科知识点讲解、题目解答、解题过程
- ❌ 不得提供拍照搜题、题库练习、作业批改功能
- ❌ 不得推荐付费教师、课程或培训机构
- ❌ 不得生成"每日复习计划""个性化复习任务"等学科辅导内容
- ✅ 可以提供里程碑时间提醒、通用行动建议、金句、错题拍照归档（不解题）、成长记录

---

## 数据模型（Data Models）

### 1. User（用户/家长）

```
Table: users
├── id: UUID (PK)
├── openid: String (微信openid, UNIQUE, NOT NULL)
├── union_id: String (微信unionid, NULLABLE)
├── nickname: String (微信昵称)
├── avatar_url: String (微信头像URL)
├── created_at: DateTime
├── updated_at: DateTime
└── is_active: Boolean (DEFAULT true)
```

### 2. Student（孩子档案）

一个家长可以有多个孩子（多孩家庭支持）。

```
Table: students
├── id: UUID (PK)
├── user_id: UUID (FK → users.id, NOT NULL)
├── name: String (孩子姓名/昵称, NOT NULL, 最长20字符)
├── grade: Enum('gao1', 'gao2', 'gao3') (年级, NOT NULL)
├── district: String (所在区, NULLABLE, 如 'huangpu', 'xuhui' 等)
│   # 上海16个区: 黄浦、徐汇、长宁、静安、普陀、虹口、杨浦、
│   #   闵行、宝山、嘉定、浦东新区、金山、松江、青浦、奉贤、崇明
├── has_selected_subjects: Boolean (是否已选科, DEFAULT false)
├── selected_subject_1: String (选考科目1, NULLABLE)
├── selected_subject_2: String (选考科目2, NULLABLE)
├── selected_subject_3: String (选考科目3, NULLABLE)
│   # 可选值: 'physics', 'chemistry', 'biology', 'politics', 'history', 'geography'
├── has_jan_english_exam: Boolean (是否报名1月外语考试, DEFAULT false, 仅高三)
├── created_at: DateTime
└── updated_at: DateTime

Constraints:
- 高一(gao1): has_selected_subjects 可为 false, selected_subject_* 可为 NULL
- 高二(gao2): has_selected_subjects 可为 true 或 false
- 高三(gao3): has_selected_subjects 必须为 true, selected_subject_* 不可为 NULL
- selected_subject_1/2/3 三者不可重复
```

### 3. Subject（科目）

系统预置，不可由用户修改。

```
Table: subjects
├── id: String (PK, 如 'chinese', 'math', 'english', 'physics' 等)
├── name: String (显示名称, 如 '语文', '数学')
├── category: Enum('required', 'elective') 
│   # required=必考大三门, elective=可选小三门
├── gaokao_max_score: Integer (高考满分: 语数外150, 小三门70)
├── display_order: Integer (显示排序)
└── icon: String (图标名称)

预置数据:
- chinese:    语文, required, 150, order=1
- math:       数学, required, 150, order=2
- english:    外语, required, 150, order=3
- physics:    物理, elective, 70,  order=4
- chemistry:  化学, elective, 70,  order=5
- biology:    生命科学, elective, 70, order=6
- politics:   政治, elective, 70,  order=7
- history:    历史, elective, 70,  order=8
- geography:  地理, elective, 70,  order=9
```

### 4. KnowledgeTree（知识点树）

三级结构，系统预置。

```
Table: knowledge_nodes
├── id: UUID (PK)
├── subject_id: String (FK → subjects.id, NOT NULL)
├── parent_id: UUID (FK → knowledge_nodes.id, NULLABLE)
│   # NULL = 一级节点（模块）
│   # 指向一级节点 = 二级节点（章节）
│   # 指向二级节点 = 三级节点（知识点）
├── level: Integer (1, 2, 3)
├── name: String (节点名称, 如 '代数', '三角函数', '倍角公式')
├── display_order: Integer (同级内排序)
└── is_active: Boolean (DEFAULT true)

索引:
- INDEX (subject_id, level)
- INDEX (parent_id)

示例数据层级:
math
├── [L1] 代数 (parent_id=NULL)
│   ├── [L2] 函数基础 
│   │   ├── [L3] 定义域/值域
│   │   ├── [L3] 单调性
│   │   └── [L3] 奇偶性
│   ├── [L2] 三角函数
│   │   ├── [L3] 正弦余弦基础
│   │   ├── [L3] 倍角/半角公式
│   │   ├── [L3] 和差化积
│   │   └── [L3] 三角函数图像与性质
│   └── [L2] 数列
│       ├── [L3] 等差数列
│       └── [L3] 等比数列
├── [L1] 几何
│   ├── [L2] 立体几何
│   └── [L2] 解析几何
└── [L1] 概率统计
    ├── [L2] 概率
    └── [L2] 统计
```

### 5. Milestone（里程碑）

系统预置 + 用户自定义。

```
Table: milestones
├── id: UUID (PK)
├── type: Enum('system', 'custom')
│   # system = 系统预置（不可删除）
│   # custom = 用户自定义
├── student_id: UUID (FK → students.id, NULLABLE)
│   # system类型时为NULL（全局共享）
│   # custom类型时关联具体学生
├── title: String (里程碑名称, NOT NULL, 最长50字符)
├── description: String (描述, NULLABLE, 最长200字符)
├── event_date: Date (事件日期, NOT NULL)
├── event_end_date: Date (结束日期, NULLABLE, 多日考试时使用)
├── category: Enum(
│     'qualification_exam',  # 合格考
│     'level_exam',          # 等级考
│     'spring_exam',         # 春季高考
│     'autumn_exam',         # 秋季高考
│     'mock_exam',           # 模拟考
│     'school_exam',         # 校内考试
│     'registration',        # 报名
│     'volunteer_fill',      # 志愿填报
│     'result_release',      # 成绩/录取发布
│     'comprehensive_eval',  # 综合评价
│     'custom'               # 自定义
│   )
├── applicable_grades: JSON Array (适用年级, 如 ['gao3'] 或 ['gao1','gao2','gao3'])
├── applicable_subjects: JSON Array (相关选考科目, NULLABLE)
│   # 如 ['physics','chemistry','biology'] 表示理科等级考
│   # NULL 表示不限科目
├── applicable_districts: JSON Array (适用区, NULLABLE)
│   # 如 ['huangpu'] 表示仅黄浦区
│   # NULL 表示全市通用
├── requires_jan_english: Boolean (是否仅对报名1月外语考试的用户展示, DEFAULT false)
├── remind_15d: Boolean (是否发送前15天提醒, DEFAULT true)
├── remind_3d: Boolean (是否发送前3天提醒, DEFAULT true)
├── action_card_15d_id: UUID (FK → action_cards.id, NULLABLE)
├── action_card_3d_id: UUID (FK → action_cards.id, NULLABLE)
├── is_dynamic_date: Boolean (日期是否需要动态更新, DEFAULT false)
├── display_order: Integer
├── created_at: DateTime
└── updated_at: DateTime

索引:
- INDEX (event_date)
- INDEX (category)
- INDEX (student_id)

预置里程碑数据（2025-2026学年高三示例）:
- 高考大报名: 2025-10-14, registration, ['gao3']
- 外语听说测试: 2025-11下旬, autumn_exam, ['gao3'], is_dynamic_date=true
- 一模(黄浦): 2025-12-04~05, mock_exam, ['gao3'], district=['huangpu']
- 一模(其他区): 2025-12月, mock_exam, ['gao3'], is_dynamic_date=true
- 合格考(第一批): 2026-01-03~04, qualification_exam, ['gao1','gao2','gao3']
- 春季高考(含外语一考): 2026-01-03~05, spring_exam, ['gao3']
- 春考志愿填报: 2026-01-30~31, volunteer_fill, ['gao3']
- 春招院校自主测试: 2026-02-28~03-01, spring_exam, ['gao3']
- 二模: 2026-03月, mock_exam, ['gao3'], is_dynamic_date=true
- 综合评价报名: 2026-04月, comprehensive_eval, ['gao3']
- 三模: 2026-04月, mock_exam, ['gao3'], is_dynamic_date=true
- 等级考(小三门): 2026-05月上旬, level_exam, ['gao3'], is_dynamic_date=true
- 等级考技能操作测试: 2026-05-19~23, level_exam, ['gao3'], 
    applicable_subjects=['physics','chemistry','biology']
- 高考语文+数学: 2026-06-07, autumn_exam, ['gao3']
- 高考外语笔试: 2026-06-08, autumn_exam, ['gao3']
- 高考外语听说: 2026-06-09, autumn_exam, ['gao3']
- 成绩公布: 2026-06月下旬, result_release, ['gao3'], is_dynamic_date=true
- 志愿填报: 2026-07月, volunteer_fill, ['gao3'], is_dynamic_date=true
- 录取结果: 2026-07月, result_release, ['gao3'], is_dynamic_date=true

高一/高二通用里程碑:
- 期中考试: 11月, school_exam, ['gao1','gao2','gao3']
- 期末考试: 1月/6月, school_exam, ['gao1','gao2','gao3']
- 合格考: 1月/6月, qualification_exam, ['gao1','gao2']
```

### 6. ActionCard（行动卡片）

系统预置的行动卡片模板。

```
Table: action_cards
├── id: UUID (PK)
├── milestone_category: Enum (关联的里程碑类别)
├── timing: Enum('15d_before', '3d_before') (触发时机)
├── title: String (卡片标题, NOT NULL)
├── description: String (卡片描述)
├── action_items: JSON Array of Objects
│   # 每个 action_item:
│   # {
│   #   "icon": "🖨️",
│   #   "text": "帮孩子打印各科核心公式/要点汇总表",
│   #   "detail": "可在知识点树中查看各科章节",
│   #   "category": "print" | "purchase" | "diet" | "sleep" | 
│   #               "transport" | "document" | "communication" | "study_method" | "errornote"
│   # }
├── footer_tip: String (底部提示语, NULLABLE)
├── applicable_grades: JSON Array
├── applicable_subjects: JSON Array (NULLABLE)
├── quote_category: String (关联的金句类别, 用于自动匹配金句)
└── created_at: DateTime

示例 - 等级考前15天行动卡片:
{
  "title": "等级考准备清单",
  "timing": "15d_before",
  "milestone_category": "level_exam",
  "action_items": [
    {"icon": "🖨️", "text": "帮孩子打印各科核心公式/要点汇总表", "detail": "可在知识点树中查看各科章节", "category": "print"},
    {"icon": "🚗", "text": "确认考试地点和交通路线", "category": "transport"},
    {"icon": "💬", "text": "和孩子聊一下：三科中哪科最想冲刺？", "category": "communication"},
    {"icon": "😴", "text": "开始调整作息，保证每晚11点前入睡", "category": "sleep"},
    {"icon": "✏️", "text": "准备好2B铅笔、黑色签字笔、橡皮等文具（备两套）", "category": "purchase"},
    {"icon": "📸", "text": "翻一下错题本，看看哪科积累最多", "detail": "重点打印错题多的章节资料", "category": "errornote"}
  ],
  "footer_tip": "跟着学校节奏走即可，不需要额外加压",
  "quote_category": "pre_exam_encouragement"
}
```

### 7. DailyQuote（每日金句）

```
Table: daily_quotes
├── id: UUID (PK)
├── content: String (金句内容, NOT NULL, 最长100字符)
├── author: String (作者, NULLABLE, 如 '李白')
├── category: Enum(
│     'daily_encouragement',    # 日常鼓励
│     'study_method',           # 学习方法
│     'pre_exam_motivation',    # 考前激励
│     'stress_relief',          # 减压放松
│     'post_exam_relief',       # 考后释然
│     'parent_child_warmth',    # 亲子温暖
│     'famous_quotes',          # 名人名言
│     'gao1_special'            # 高一专属
│   )
├── applicable_grades: JSON Array (适用年级, 如 ['gao1'] 或 ['gao1','gao2','gao3'])
├── applicable_phase: Enum('normal', 'pre_exam_30d', 'pre_exam_7d', 'post_exam', 'all')
│   # 阶段感知: 距考试>30天=normal, 15-30天=pre_exam_30d, <7天=pre_exam_7d, 考后=post_exam
├── display_order: Integer (用于控制展示顺序)
├── is_active: Boolean (DEFAULT true)
└── created_at: DateTime

预置数据量: 300+ 条，确保高中三年不重复
```

### 8. UserQuoteFavorite（金句收藏）

```
Table: user_quote_favorites
├── id: UUID (PK)
├── user_id: UUID (FK → users.id, NOT NULL)
├── quote_id: UUID (FK → daily_quotes.id, NOT NULL)
├── created_at: DateTime

Constraints:
- UNIQUE (user_id, quote_id)
```

### 9. UserQuoteHistory（金句展示历史）

```
Table: user_quote_history
├── id: UUID (PK)
├── student_id: UUID (FK → students.id, NOT NULL)
├── quote_id: UUID (FK → daily_quotes.id, NOT NULL)
├── display_date: Date (展示日期, NOT NULL)

Constraints:
- UNIQUE (student_id, display_date)  # 每个孩子每天只展示一条

索引:
- INDEX (student_id, display_date)
```

### 10. Exam（考试成绩记录）

```
Table: exams
├── id: UUID (PK)
├── student_id: UUID (FK → students.id, NOT NULL)
├── name: String (考试名称, NOT NULL, 最长50字符, 如 '高三期中考试')
├── exam_type: Enum('monthly', 'midterm', 'final', 'mock1', 'mock2', 'mock3', 'other')
├── exam_date: Date (考试时间, NOT NULL)
├── created_at: DateTime
└── updated_at: DateTime

索引:
- INDEX (student_id, exam_date)
```

### 11. ExamScore（单科成绩）

```
Table: exam_scores
├── id: UUID (PK)
├── exam_id: UUID (FK → exams.id, NOT NULL)
├── subject_id: String (FK → subjects.id, NOT NULL)
├── score: Decimal(5,1) (得分, NOT NULL, >= 0)
├── max_score: Decimal(5,1) (该次考试该科满分, NOT NULL, > 0)
│   # 满分可自定义: 校内考试满分可能是75、80、100、150等
├── score_rate: Decimal(5,2) (得分率 = score/max_score * 100, 自动计算)
└── created_at: DateTime

Constraints:
- UNIQUE (exam_id, subject_id)
- score <= max_score
- max_score BETWEEN 10 AND 300

索引:
- INDEX (exam_id)

业务规则:
- 高一(未选科): 展示全部9科输入框
- 高二/高三(已选科): 仅展示6科（3必考+3选考）输入框
- max_score 默认值: 
  - 大三门默认150, 小三门默认100
  - 用户可修改, 修改后同科目下次录入沿用上次值
```

### 12. ErrorNote（错题记录）

```
Table: error_notes
├── id: UUID (PK)
├── student_id: UUID (FK → students.id, NOT NULL)
├── subject_id: String (FK → subjects.id, NOT NULL)
├── knowledge_node_id: UUID (FK → knowledge_nodes.id, NULLABLE)
│   # 关联知识点(二级或三级), 可不选
├── error_type: Enum('careless', 'concept_unclear', 'method_unknown', 'other')
│   # 粗心 / 概念不清 / 方法不会 / 其他
│   # NULLABLE - 可不选
├── source: Enum('monthly', 'weekly', 'homework', 'mock', 'other')
│   # 月考 / 周测 / 作业 / 模考 / 其他
│   # NULLABLE - 可不选
├── question_image_url: String (题目照片URL, NOT NULL)
│   # 存储在对象存储(COS), 路径格式: /errors/{student_id}/{year}/{month}/{uuid}.jpg
├── correction_image_url: String (订正照片URL, NULLABLE)
├── note: String (备注, NULLABLE, 最长200字符)
├── created_at: DateTime
└── updated_at: DateTime

索引:
- INDEX (student_id, subject_id)
- INDEX (student_id, created_at DESC)
- INDEX (student_id, knowledge_node_id)

业务规则:
- 图片上传时自动压缩(最大宽度1200px, 质量80%)
- 图片加密存储, 不用于任何商业用途
- 免费版限制: 最多保存10道错题
- 标准版: 无限制
```

### 13. GrowthRecord（成长记录）

```
Table: growth_records
├── id: UUID (PK)
├── student_id: UUID (FK → students.id, NOT NULL)
├── record_type: Enum('award', 'progress', 'performance', 'breakthrough', 'memo')
│   # 🏆奖项荣誉 / 📈成绩进步 / ⭐特殊表现 / 💪突破时刻 / 📝家长备忘
├── title: String (标题, NOT NULL, 最长100字符)
├── description: String (详细描述, NULLABLE, 最长500字符)
├── record_date: Date (记录日期, NOT NULL)
├── category: Enum('academic_competition', 'sports', 'comprehensive', 'social_practice', 'other')
│   # 学科竞赛 / 文体活动 / 综合荣誉 / 社会实践 / 其他
│   # NULLABLE - 非奖项类型时可不选
├── awarding_body: String (颁奖机构, NULLABLE, 最长100字符)
├── image_url: String (证书/奖状照片URL, NULLABLE)
├── auto_generated: Boolean (是否由系统自动检测生成, DEFAULT false)
│   # 成绩进步超过阈值时系统自动提示生成
├── linked_quote_id: UUID (FK → daily_quotes.id, NULLABLE)
│   # 保存时系统自动匹配一条金句
├── created_at: DateTime
└── updated_at: DateTime

索引:
- INDEX (student_id, record_date DESC)
- INDEX (student_id, record_type)

业务规则:
- 免费版限制: 最多保存5条
- 标准版: 无限制
- 成绩进步自动检测阈值: 同类考试同科目得分率提升 >= 10个百分点
```

### 14. MilestoneReminder（提醒发送记录）

```
Table: milestone_reminders
├── id: UUID (PK)
├── student_id: UUID (FK → students.id, NOT NULL)
├── milestone_id: UUID (FK → milestones.id, NOT NULL)
├── timing: Enum('15d_before', '3d_before')
├── sent_at: DateTime (发送时间)
├── opened: Boolean (是否打开查看, DEFAULT false)
├── opened_at: DateTime (打开时间, NULLABLE)
├── action_items_checked: JSON Array (已勾选的行动项索引, DEFAULT [])

Constraints:
- UNIQUE (student_id, milestone_id, timing)
```

### 15. SchoolProgress（学校复习进度记录）

```
Table: school_progress
├── id: UUID (PK)
├── student_id: UUID (FK → students.id, NOT NULL)
├── subject_id: String (FK → subjects.id, NOT NULL)
├── content: String (复习内容, NOT NULL, 最长200字符)
│   # 如 "下两周重点：解析几何"
├── start_date: Date (开始日期, NULLABLE)
├── end_date: Date (结束日期, NULLABLE)
├── knowledge_node_id: UUID (FK → knowledge_nodes.id, NULLABLE)
│   # 关联知识点章节
├── created_at: DateTime
└── updated_at: DateTime
```

### 16. UserSubscription（用户订阅/付费状态）

```
Table: user_subscriptions
├── id: UUID (PK)
├── user_id: UUID (FK → users.id, NOT NULL)
├── plan: Enum('free', 'standard', 'premium')
├── billing_type: Enum('monthly', 'yearly', 'lifetime_high_school')
│   # monthly=月付, yearly=年付, lifetime_high_school=高中全程包
├── price_paid: Decimal(7,2) (实际支付金额)
├── started_at: DateTime
├── expires_at: DateTime (NULLABLE, lifetime_high_school时为孩子高考年份7月31日)
├── is_trial: Boolean (是否试用期, DEFAULT false)
├── trial_expires_at: DateTime (试用到期时间, NULLABLE)
├── auto_renew: Boolean (DEFAULT false)
├── created_at: DateTime
└── updated_at: DateTime

索引:
- INDEX (user_id, plan)

业务规则:
- 新用户默认 plan='free'
- 注册后自动开启7天标准版试用 (is_trial=true)
- 高中全程包 expires_at = 孩子最晚高考年份的7月31日
- 付费定价:
  - standard monthly: 19.9
  - standard yearly: 199
  - standard lifetime_high_school: 399
  - premium monthly: 39.9
  - premium yearly: 399
```

---

## API 设计（RESTful Endpoints）

### 认证

```
POST /api/auth/wx-login
  Body: { code: String (wx.login获取的code) }
  Response: { token: String (JWT), user: UserObject, is_new_user: Boolean }

说明:
- 用 wx.login code 换取 openid
- 如果是新用户, 自动创建 user 记录, 返回 is_new_user=true
- 返回 JWT token, 后续请求放在 Header Authorization: Bearer {token}
```

### 学生档案

```
POST /api/students
  Body: {
    name: String,
    grade: 'gao1' | 'gao2' | 'gao3',
    district: String (optional),
    has_selected_subjects: Boolean,
    selected_subjects: String[] (optional, 3个科目id),
    has_jan_english_exam: Boolean (optional, 仅高三)
  }
  Response: { student: StudentObject }
  说明: 创建孩子档案

GET /api/students
  Response: { students: StudentObject[] }
  说明: 获取当前用户的所有孩子档案

PUT /api/students/:id
  Body: (同POST, 所有字段optional)
  Response: { student: StudentObject }
  说明: 更新孩子信息(如选科变更、升年级)

DELETE /api/students/:id
  Response: { success: Boolean }
```

### 里程碑

```
GET /api/students/:studentId/milestones
  Query: {
    upcoming_days: Integer (optional, 默认365, 未来X天内的里程碑),
    category: String (optional, 筛选类别),
    include_past: Boolean (optional, 默认false, 是否包含已过去的)
  }
  Response: {
    milestones: [{
      ...MilestoneObject,
      days_remaining: Integer,  # 距离天数(负数表示已过去)
      is_applicable: Boolean,   # 是否适用于该学生(基于年级/选科/区)
      action_card_15d: ActionCardObject | null,
      action_card_3d: ActionCardObject | null,
      reminder_status: {  # 该学生的提醒状态
        reminded_15d: Boolean,
        reminded_3d: Boolean,
        opened_15d: Boolean,
        opened_3d: Boolean
      }
    }]
  }
  说明: 
  - 自动根据学生的年级、选科、所在区、是否报名1月外语考试筛选适用的里程碑
  - 包含倒计时天数计算
  - 包含行动卡片关联

GET /api/students/:studentId/milestones/next
  Response: {
    next_milestone: MilestoneObject (最近的下一个里程碑),
    days_remaining: Integer,
    next_action_card: ActionCardObject | null (如果在15天或3天窗口内)
  }
  说明: 获取最近的下一个里程碑, 用于首页展示

POST /api/students/:studentId/milestones
  Body: {
    title: String,
    event_date: Date,
    event_end_date: Date (optional),
    category: 'custom',
    description: String (optional)
  }
  Response: { milestone: MilestoneObject }
  说明: 创建自定义里程碑

PUT /api/students/:studentId/milestones/:id
  说明: 仅可修改 custom 类型

DELETE /api/students/:studentId/milestones/:id
  说明: 仅可删除 custom 类型
```

### 里程碑提醒

```
POST /api/students/:studentId/reminders/:reminderId/opened
  Response: { success: Boolean }
  说明: 标记提醒已打开

PUT /api/students/:studentId/reminders/:reminderId/actions
  Body: { checked_indexes: Integer[] }
  Response: { success: Boolean }
  说明: 更新行动项勾选状态
```

### 每日金句

```
GET /api/students/:studentId/quote/today
  Response: {
    quote: QuoteObject,
    is_favorited: Boolean
  }
  说明:
  - 返回今天的金句
  - 如果今天还没有分配金句, 自动按规则选择一条:
    1. 根据学生年级筛选 applicable_grades
    2. 根据距最近考试天数匹配 applicable_phase
    3. 排除已展示过的 (查 user_quote_history)
    4. 按 display_order 排序, 取第一条
    5. 记录到 user_quote_history

POST /api/quotes/:quoteId/favorite
  Response: { success: Boolean }
  说明: 收藏金句

DELETE /api/quotes/:quoteId/favorite
  Response: { success: Boolean }
  说明: 取消收藏

GET /api/quotes/favorites
  Response: { quotes: QuoteObject[] }
  说明: 获取所有收藏的金句

GET /api/students/:studentId/quote/share-image
  Query: { quote_id: UUID }
  Response: { image_url: String (生成的分享图片URL) }
  说明: 生成金句分享图片(含倒计时+金句+小程序码)
```

### 知识点树

```
GET /api/students/:studentId/knowledge-tree
  Query: {
    subject_id: String (optional, 指定科目),
    level: Integer (optional, 1|2|3, 默认返回到2级)
  }
  Response: {
    subjects: [{
      subject: SubjectObject,
      tree: KnowledgeNodeObject[] (嵌套结构)
    }]
  }
  说明:
  - 高一: 返回全部9科
  - 高二/高三: 返回6科(3必考+3选考)
  - level=2 时三级节点不包含在返回中(前端按需展开加载)

GET /api/knowledge-tree/:subjectId/:parentNodeId/children
  Response: { children: KnowledgeNodeObject[] }
  说明: 按需加载某个二级节点下的三级子节点(用于前端展开操作)
```

### 成绩记录

```
POST /api/students/:studentId/exams
  Body: {
    name: String,
    exam_type: String,
    exam_date: Date,
    scores: [{
      subject_id: String,
      score: Number,
      max_score: Number
    }]
  }
  Response: {
    exam: ExamObject (含scores),
    progress_detected: [{  # 自动检测到的进步
      subject_id: String,
      subject_name: String,
      previous_rate: Number,
      current_rate: Number,
      improvement: Number  # 百分点提升
    }] | null
  }
  说明:
  - 自动计算 score_rate
  - 自动对比上次同类型考试, 检测进步(提升>=10个百分点)
  - 如有进步, 返回 progress_detected, 前端提示"是否记录到成长册"

GET /api/students/:studentId/exams
  Query: {
    subject_id: String (optional),
    exam_type: String (optional),
    limit: Integer (optional, 默认20)
  }
  Response: { exams: ExamObject[] (含scores) }

GET /api/students/:studentId/exams/trend
  Query: { subject_id: String (必填) }
  Response: {
    trend: [{
      exam_name: String,
      exam_date: Date,
      score: Number,
      max_score: Number,
      score_rate: Number
    }],
    overall_trend: 'up' | 'down' | 'stable',
    best_rate: Number,
    latest_rate: Number
  }
  说明: 返回指定科目的成绩趋势数据, 用于绘制折线图

GET /api/students/:studentId/exams/last-max-scores
  Response: { 
    last_max_scores: { [subject_id]: Number }
  }
  说明: 返回各科目最近一次录入时使用的满分值, 用于下次录入时的默认值

PUT /api/students/:studentId/exams/:examId
  说明: 修改考试信息和成绩

DELETE /api/students/:studentId/exams/:examId
  说明: 删除考试记录
```

### 错题本

```
POST /api/students/:studentId/error-notes
  Body: {
    subject_id: String,
    knowledge_node_id: UUID (optional),
    error_type: String (optional),
    source: String (optional),
    note: String (optional),
    question_image: File (图片文件),
    correction_image: File (optional, 图片文件)
  }
  Content-Type: multipart/form-data
  Response: { error_note: ErrorNoteObject }
  说明:
  - 图片自动压缩后上传到对象存储
  - 免费版检查: 如果已有10道错题, 返回 403 + { limit_reached: true }

GET /api/students/:studentId/error-notes
  Query: {
    subject_id: String (optional),
    knowledge_node_id: UUID (optional),
    error_type: String (optional),
    source: String (optional),
    page: Integer (默认1),
    page_size: Integer (默认20),
    sort: 'newest' | 'oldest' (默认 'newest')
  }
  Response: {
    error_notes: ErrorNoteObject[],
    total: Integer,
    page: Integer,
    page_size: Integer,
    stats: {  # 错题统计
      total_count: Integer,
      by_subject: { [subject_id]: Integer },
      by_error_type: { [error_type]: Integer }
    }
  }

GET /api/students/:studentId/error-notes/:id
  Response: { error_note: ErrorNoteObject (含完整图片URL) }

DELETE /api/students/:studentId/error-notes/:id
  Response: { success: Boolean }

GET /api/students/:studentId/error-notes/stats
  Response: {
    total_count: Integer,
    by_subject: [{ subject_id: String, subject_name: String, count: Integer }],
    by_error_type: [{ error_type: String, count: Integer }],
    by_knowledge_node: [{ node_id: UUID, node_name: String, subject_name: String, count: Integer }]
  }
  说明: 错题统计数据, 用于首页展示和行动卡片联动
```

### 成长记录

```
POST /api/students/:studentId/growth-records
  Body: {
    record_type: String,
    title: String,
    description: String (optional),
    record_date: Date,
    category: String (optional),
    awarding_body: String (optional),
    image: File (optional, 证书照片),
    auto_generated: Boolean (optional, 默认false)
  }
  Content-Type: multipart/form-data
  Response: {
    growth_record: GrowthRecordObject,
    matched_quote: QuoteObject (系统自动匹配的金句)
  }
  说明:
  - 保存时自动匹配一条鼓励类金句
  - 免费版检查: 如果已有5条, 返回 403 + { limit_reached: true }

GET /api/students/:studentId/growth-records
  Query: {
    record_type: String (optional),
    year: Integer (optional, 学年),
    page: Integer (默认1),
    page_size: Integer (默认50)
  }
  Response: {
    growth_records: GrowthRecordObject[],
    total: Integer,
    by_school_year: {  # 按学年分组
      '2025-2026': GrowthRecordObject[],
      '2024-2025': GrowthRecordObject[]
    }
  }

DELETE /api/students/:studentId/growth-records/:id
  Response: { success: Boolean }

GET /api/students/:studentId/growth-records/export
  Response: { pdf_url: String } | { image_url: String }
  说明: 导出成长档案(PDF或长图), 仅标准版及以上
```

### 学校进度

```
POST /api/students/:studentId/school-progress
  Body: {
    subject_id: String,
    content: String,
    start_date: Date (optional),
    end_date: Date (optional),
    knowledge_node_id: UUID (optional)
  }
  Response: {
    school_progress: SchoolProgressObject,
    linked_suggestions: [{
      type: 'error_note_count',
      message: '该章节有X道错题，可提醒孩子复习前翻一下错题本'
    }] | null
  }
  说明: 保存后自动检查该知识点是否有关联错题, 返回联动提示

GET /api/students/:studentId/school-progress
  Query: { subject_id: String (optional) }
  Response: { school_progress: SchoolProgressObject[] }
```

### 订阅管理

```
GET /api/subscription
  Response: {
    plan: String,
    billing_type: String,
    expires_at: DateTime,
    is_trial: Boolean,
    trial_expires_at: DateTime,
    limits: {
      error_notes_max: Integer | null (null=无限制),
      error_notes_used: Integer,
      growth_records_max: Integer | null,
      growth_records_used: Integer,
      can_expand_knowledge_l3: Boolean,
      can_share_quote_image: Boolean,
      can_use_widget: Boolean,
      can_export_growth: Boolean,
      can_view_exam_trend: Boolean,
      has_action_cards: Boolean
    }
  }

POST /api/subscription/upgrade
  Body: {
    plan: 'standard' | 'premium',
    billing_type: 'monthly' | 'yearly' | 'lifetime_high_school'
  }
  Response: { payment_params: Object (微信支付参数) }
  说明: 调起微信支付
```

### 首页聚合接口

```
GET /api/students/:studentId/dashboard
  Response: {
    today_quote: {
      quote: QuoteObject,
      is_favorited: Boolean
    },
    countdowns: {
      nearest_exam: { title: String, days: Integer, date: Date },
      gaokao: { days: Integer, date: Date } | null  # 高三才有
    },
    active_action_card: ActionCardObject | null,
    # 如果当前处于某个里程碑的15天或3天窗口内, 返回对应行动卡片
    upcoming_milestones: MilestoneObject[] (未来30天内),
    error_notes_summary: { total: Integer, top_subject: String, top_count: Integer },
    growth_records_count: Integer,
    subscription: SubscriptionSummary
  }
  说明: 首页一次性拉取所有需要的数据, 减少请求数
```

---

## 页面结构与交互规范（Pages & Interactions）

### 页面列表

```
pages/
├── index/index                  # 首页(倒计时+金句+行动提醒+入口)
├── onboarding/welcome           # 欢迎页
├── onboarding/grade-select      # 选择年级
├── onboarding/subject-select    # 选科(高二/高三)
├── onboarding/english-exam      # 是否报名1月外语考试(高三)
├── onboarding/district-select   # 选择所在区(可选)
├── onboarding/complete          # 引导添加桌面+完成
├── milestones/timeline          # 里程碑时间线(完整)
├── milestones/action-card       # 行动卡片详情
├── milestones/add-custom        # 添加自定义里程碑
├── knowledge/browse             # 知识点树浏览
├── exams/list                   # 成绩列表
├── exams/add                    # 录入成绩
├── exams/trend                  # 成绩趋势图
├── errors/list                  # 错题本列表
├── errors/add                   # 拍照录入错题
├── errors/detail                # 错题详情(大图)
├── growth/timeline              # 成长记录时间线
├── growth/add                   # 添加成长记录
├── growth/export                # 导出成长档案
├── quotes/favorites             # 金句收藏列表
├── profile/index                # 个人中心
├── profile/student-manage       # 孩子档案管理
├── profile/subscription         # 订阅管理
├── profile/privacy              # 隐私政策
└── profile/about                # 关于我们
```

### 首页交互规范（index/index）

```
┌──────────────────────────────────┐
│  [首页]  [错题📸]  [成长🏆]  [我的] │  ← 底部TabBar, 4个Tab
├──────────────────────────────────┤
│                                  │
│  ✨ {today_quote.content}         │  ← 金句区域
│  {today_quote.author || ''}       │     点击[❤️]收藏, 点击[分享]生成图片
│                [收藏❤️] [分享📤]  │
│                                  │
│  ┌─────────────┬────────────┐   │  ← 倒计时区域(双倒计时)
│  │ 📅 距{nearest}│ 📅 距高考   │   │     高一/高二: 只显示nearest
│  │   {N} 天     │   {N} 天   │   │     高三: 显示nearest+高考
│  └─────────────┴────────────┘   │     点击进入里程碑时间线
│                                  │
│  📋 {action_card.title}      [→] │  ← 行动提醒区域(条件展示)
│  {剩余X天, 查看准备清单}          │     仅在里程碑前15天/3天窗口内展示
│                                  │     点击进入行动卡片详情
│  ─── 或 ───                      │     如无活跃行动卡片, 展示下方
│  🗓️ 近期里程碑                    │     最近2-3个里程碑摘要
│  • {milestone.title} ({N}天后)   │     点击进入时间线
│                                  │
│  ──── 快捷入口 ────              │  ← 功能入口区域
│  📸 错题本({N}道)           [→]  │
│  🏆 成长记录({N}个闪光时刻) [→]  │
│  📚 知识点浏览              [→]  │
│  📊 成绩记录                [→]  │
│                                  │
│  [📱 添加到桌面]                  │  ← 仅未添加时展示
│                                  │
└──────────────────────────────────┘

数据加载:
- 页面 onLoad 调用 GET /api/students/:studentId/dashboard
- 如果有多个孩子, 顶部显示孩子切换器
- 下拉刷新重新加载

首页不展示的内容(重要):
- ❌ 不展示"还有X个薄弱点未解决"等焦虑式指标
- ❌ 不展示"您已X天未使用"等催促提示
- ❌ 不展示任何横向对比数据
```

### Onboarding流程交互规范

```
欢迎页(onboarding/welcome):
- 展示: "高考路上，你不是一个人。" + 简短介绍
- 按钮: [开始使用]
- 点击后检查微信登录状态

年级选择(onboarding/grade-select):
- 三个大按钮: [高一] [高二] [高三]
- 点击后:
  - 高一 → 跳转 district-select(跳过选科)
  - 高二 → 询问"是否已选科?" [已选科→subject-select] [还没选→district-select]
  - 高三 → 跳转 subject-select

选科(onboarding/subject-select):
- 展示6个科目按钮: 物理/化学/生命科学/政治/历史/地理
- 必须选择恰好3个
- 选中状态高亮, 超过3个时最早选的自动取消
- 底部: [确认]

外语一考(onboarding/english-exam): (仅高三)
- "孩子是否报名1月外语考试?"
- [是] [否] [还不确定]
- "还不确定"按否处理, 后续可在设置中修改

区选择(onboarding/district-select): (可选)
- "选择所在区(用于匹配模考时间)"
- 16个区的列表
- [暂不选择] 跳过

完成(onboarding/complete):
- 展示: 个性化里程碑时间线预览 + 今日金句
- 引导: "把倒计时和金句放在手机桌面"
- [添加到桌面] [稍后再说]
- 进入首页
```

### 错题录入交互规范（errors/add）

```
Step 1: 拍照/选图
- 点击拍照按钮调用 wx.chooseMedia
- 支持拍照或从相册选取
- 最多选2张(题目照片 + 订正照片)
- 图片预览, 支持重拍

Step 2: 选择科目
- 展示当前年级对应的科目按钮(高一9科, 高二/高三6科)
- 必选

Step 3: 选择知识点(可选)
- 展示该科目的知识点树(默认2级)
- 可展开到3级(标准版)
- 点选一个节点即可
- [跳过] 不选也行

Step 4: 标注信息(全部可选)
- 错误类型: [粗心] [概念不清] [方法不会] [其他]
- 来源: [月考] [周测] [作业] [模考] [其他]
- 备注: 文本输入框, 最长200字

Step 5: 保存
- 调用 POST /api/students/:studentId/error-notes
- 成功后返回错题列表
- 免费版达到10道上限时, 弹窗提示升级
```

### 行动卡片详情交互规范（milestones/action-card）

```
页面结构:
- 顶部: 标题 + 倒计时天数
- 中部: 相关信息(选考科目等)
- 主体: 行动清单(可勾选checkbox)
  - 每个行动项包含图标+文字+详情(可选)
  - 勾选后调用 PUT /api/.../actions 保存状态
  - 勾选动画: 打勾+文字变灰
- 底部: 提示语 + 金句
- 行动项中如包含"翻一下错题本", 点击可直接跳转错题本页面
- 行动项中如包含"查看知识点树", 点击可跳转知识点浏览

行动项勾选:
- 勾选状态持久化存储(调API)
- 再次打开时恢复勾选状态
- 所有项勾选完成时, 展示"✅ 准备就绪!" + 鼓励金句
```

---

## 功能权限矩阵（Feature Access Matrix）

```
| 功能                      | 免费版        | 标准版(¥19.9/月) | 高级版(¥39.9/月) |
|--------------------------|--------------|-----------------|-----------------|
| 倒计时                    | ✅            | ✅               | ✅               |
| 里程碑时间线浏览            | ✅            | ✅               | ✅               |
| 每日金句(基础库50条)        | ✅            | —                | —                |
| 每日金句(完整库300+条)      | ❌            | ✅               | ✅               |
| 知识点树(2级)              | ✅            | ✅               | ✅               |
| 知识点树(3级展开)           | ❌            | ✅               | ✅               |
| 成绩记录(最多3次)          | ✅            | —                | —                |
| 成绩记录(无限)             | ❌            | ✅               | ✅               |
| 成绩趋势分析图             | ❌            | ✅               | ✅               |
| 错题本(最多10道)           | ✅            | —                | —                |
| 错题本(无限)               | ❌            | ✅               | ✅               |
| 成长记录(最多5条)          | ✅            | —                | —                |
| 成长记录(无限)             | ❌            | ✅               | ✅               |
| 成长档案导出               | ❌            | ✅               | ✅               |
| 里程碑行动卡片             | ❌            | ✅               | ✅               |
| 桌面快捷方式/小组件        | ❌            | ✅               | ✅               |
| 金句收藏                   | ❌            | ✅               | ✅               |
| 金句分享图片生成            | ❌            | ✅               | ✅               |
| 学校进度记录+联动           | ❌            | ✅               | ✅               |
| AI家长顾问                 | ❌            | ❌               | ✅               |
| AI个性化行动建议            | ❌            | ❌               | ✅               |
| AI个性化金句               | ❌            | ❌               | ✅               |
| AI错题分类助手              | ❌            | ❌               | ✅ (需合规确认)   |
| AI月度成长报告              | ❌            | ❌               | ✅               |
```

---

## 定时任务与后台逻辑（Background Jobs）

### 1. 每日金句分配（每日 08:00）

```
Job: assign_daily_quotes
Schedule: 每天 08:00
逻辑:
  FOR each active student:
    1. 获取 student.grade
    2. 计算距最近考试天数 → 确定 applicable_phase
    3. 查询 daily_quotes WHERE:
       - applicable_grades CONTAINS student.grade
       - applicable_phase = 计算出的phase OR applicable_phase = 'all'
       - id NOT IN (SELECT quote_id FROM user_quote_history WHERE student_id = student.id)
       - is_active = true
    4. ORDER BY display_order, RANDOM()
    5. 取第一条, INSERT INTO user_quote_history
    6. 如果没有未展示的金句(全部展示过), 重置历史重新循环
```

### 2. 里程碑提醒检查（每日 09:00）

```
Job: check_milestone_reminders
Schedule: 每天 09:00
逻辑:
  FOR each active student:
    1. 获取该学生适用的所有里程碑(基于年级/选科/区)
    2. FOR each milestone:
       a. 计算 days_remaining = milestone.event_date - today
       b. IF days_remaining == 15 AND milestone.remind_15d == true:
          - 检查是否已发送过(查 milestone_reminders)
          - 如未发送: INSERT reminder, 发送微信模板消息/订阅消息
       c. IF days_remaining == 3 AND milestone.remind_3d == true:
          - 同上
    3. 发送的消息内容:
       - 标题: "{milestone.title} 倒计时{N}天"
       - 描述: "查看家长准备清单"
       - 跳转: milestones/action-card?id={milestone.id}&timing={15d|3d}
```

### 3. 成绩进步自动检测（成绩录入时触发）

```
Trigger: POST /api/students/:studentId/exams 成功后
逻辑:
  FOR each score in new_exam.scores:
    1. 查找上一次同 exam_type 的同科目成绩
    2. IF 上次存在:
       improvement = current_score_rate - previous_score_rate
       IF improvement >= 10:  # 提升10个百分点以上
         返回 progress_detected 数组
    3. 前端收到 progress_detected 后弹窗:
       "🎉 数学进步了{improvement}个百分点！要记录到成长册吗？"
       [记录进步🏆] [下次再说]
       点击[记录进步] → 自动跳转 growth/add, 预填信息
```

### 4. 图片清理（每周日 03:00）

```
Job: cleanup_orphan_images
Schedule: 每周日 03:00
逻辑:
  1. 扫描对象存储中超过24小时但未关联到任何 error_note 或 growth_record 的图片
  2. 删除这些孤立图片
  说明: 用户拍照后未保存的图片需要清理
```

---

## 错误处理规范（Error Handling）

```
所有API错误响应格式:
{
  "error": {
    "code": String,          # 错误码
    "message": String,       # 用户可见的中文错误信息
    "detail": String         # 开发调试用的详细信息(生产环境不返回)
  }
}

错误码定义:
| HTTP Status | Code                    | Message                        | 场景                    |
|------------|-------------------------|--------------------------------|------------------------|
| 400        | INVALID_PARAMS          | 请求参数有误                     | 参数校验失败             |
| 400        | INVALID_SUBJECT_COUNT   | 请选择恰好3门选考科目             | 选科数量不对             |
| 400        | DUPLICATE_SUBJECTS      | 选考科目不能重复                  | 选了重复科目             |
| 400        | SCORE_EXCEEDS_MAX       | 得分不能超过满分                  | score > max_score      |
| 401        | UNAUTHORIZED            | 请先登录                        | token无效或过期          |
| 403        | FREE
好的，以下是从中断处（错误处理规范的 `403 FREE` 行）开始的**完整补全内容**，一直到 `spec.md` 文档结尾：

---

```markdown
错误码定义(续):
| HTTP Status | Code                    | Message                        | 场景                    |
|------------|-------------------------|--------------------------------|------------------------|
| 400        | INVALID_PARAMS          | 请求参数有误                     | 参数校验失败             |
| 400        | INVALID_SUBJECT_COUNT   | 请选择恰好3门选考科目             | 选科数量不对             |
| 400        | DUPLICATE_SUBJECTS      | 选考科目不能重复                  | 选了重复科目             |
| 400        | SCORE_EXCEEDS_MAX       | 得分不能超过满分                  | score > max_score      |
| 400        | INVALID_MAX_SCORE       | 满分需在10-300之间               | max_score范围校验       |
| 400        | GRADE_REQUIRES_SUBJECTS | 高三必须选择等级考科目             | 高三未选科               |
| 401        | UNAUTHORIZED            | 请先登录                        | token无效或过期          |
| 403        | FREE_LIMIT_ERROR_NOTES  | 免费版最多保存10道错题，升级解锁无限存储 | 错题数达上限            |
| 403        | FREE_LIMIT_GROWTH       | 免费版最多保存5条成长记录，升级解锁无限记录 | 成长记录达上限          |
| 403        | FREE_LIMIT_EXAMS        | 免费版最多记录3次考试，升级解锁无限记录   | 考试记录达上限          |
| 403        | FEATURE_REQUIRES_STANDARD | 此功能需要标准版，升级后即可使用    | 访问标准版功能           |
| 403        | FEATURE_REQUIRES_PREMIUM  | 此功能需要高级版，升级后即可使用    | 访问高级版功能           |
| 403        | CANNOT_DELETE_SYSTEM_MILESTONE | 系统预置里程碑不可删除         | 删除系统里程碑           |
| 404        | STUDENT_NOT_FOUND       | 未找到该学生档案                  | student_id无效          |
| 404        | RESOURCE_NOT_FOUND      | 未找到该资源                     | 通用404                |
| 409        | DUPLICATE_EXAM_DATE     | 该日期已有同名考试记录             | 重复录入                |
| 413        | IMAGE_TOO_LARGE         | 图片大小不能超过10MB              | 上传图片过大             |
| 429        | RATE_LIMIT_EXCEEDED     | 操作太频繁，请稍后再试             | 频率限制                |
| 500        | INTERNAL_ERROR          | 系统繁忙，请稍后再试              | 服务端异常               |

前端错误处理规范:
- 403 FREE_LIMIT_* 错误: 弹出升级引导弹窗, 展示付费方案
- 403 FEATURE_REQUIRES_* 错误: 弹出功能介绍+升级引导
- 401 UNAUTHORIZED: 自动跳转微信登录流程
- 500 INTERNAL_ERROR: 展示友好的错误页面 + 重试按钮
- 网络错误: 展示"网络不给力，请检查网络后重试"
```

---

## 图片处理规范（Image Processing）

```
上传流程:
1. 前端调用 wx.chooseMedia({ count: 2, mediaType: ['image'] })
2. 前端压缩图片:
   - 最大宽度: 1200px
   - 质量: 80%
   - 格式: JPEG
   - 使用 wx.compressImage 或 canvas 压缩
3. 调用 POST /api/upload/image 获取上传凭证
4. 直传到对象存储(腾讯云COS)
5. 将返回的 image_url 放入错题/成长记录的创建请求中

存储路径规范:
- 错题图片: /errors/{student_id}/{year}/{month}/{uuid}.jpg
- 错题订正: /errors/{student_id}/{year}/{month}/{uuid}_correction.jpg
- 成长证书: /growth/{student_id}/{year}/{uuid}.jpg
- 金句分享: /shares/{user_id}/{date}_{quote_id}.png (临时, 7天后清理)

安全规范:
- 所有图片URL使用带签名的临时链接, 有效期2小时
- 不使用公开可访问的URL
- 图片不做任何AI分析(Phase 1-2, 合规要求)
- 用户删除错题/成长记录时, 同步删除对象存储中的图片

存储限制:
- 单张图片最大: 10MB(压缩前) → 约1-2MB(压缩后)
- 免费版: 错题10道(最多20张图) + 成长记录5条(最多5张图)
- 标准版: 无数量限制, 单用户总存储上限500MB
- 高级版: 无数量限制, 单用户总存储上限2GB
```

---

## 微信小程序特定配置（WeChat Mini Program Config）

### app.json

```json
{
  "pages": [
    "pages/index/index",
    "pages/onboarding/welcome",
    "pages/onboarding/grade-select",
    "pages/onboarding/subject-select",
    "pages/onboarding/english-exam",
    "pages/onboarding/district-select",
    "pages/onboarding/complete",
    "pages/milestones/timeline",
    "pages/milestones/action-card",
    "pages/milestones/add-custom",
    "pages/knowledge/browse",
    "pages/exams/list",
    "pages/exams/add",
    "pages/exams/trend",
    "pages/errors/list",
    "pages/errors/add",
    "pages/errors/detail",
    "pages/growth/timeline",
    "pages/growth/add",
    "pages/growth/export",
    "pages/quotes/favorites",
    "pages/profile/index",
    "pages/profile/student-manage",
    "pages/profile/subscription",
    "pages/profile/privacy",
    "pages/profile/about"
  ],
  "tabBar": {
    "color": "#999999",
    "selectedColor": "#4A90D9",
    "backgroundColor": "#ffffff",
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页",
        "iconPath": "assets/tab-home.png",
        "selectedIconPath": "assets/tab-home-active.png"
      },
      {
        "pagePath": "pages/errors/list",
        "text": "错题本",
        "iconPath": "assets/tab-errors.png",
        "selectedIconPath": "assets/tab-errors-active.png"
      },
      {
        "pagePath": "pages/growth/timeline",
        "text": "成长册",
        "iconPath": "assets/tab-growth.png",
        "selectedIconPath": "assets/tab-growth-active.png"
      },
      {
        "pagePath": "pages/profile/index",
        "text": "我的",
        "iconPath": "assets/tab-profile.png",
        "selectedIconPath": "assets/tab-profile-active.png"
      }
    ]
  },
  "window": {
    "navigationBarBackgroundColor": "#4A90D9",
    "navigationBarTitleText": "高考家长帮",
    "navigationBarTextStyle": "white",
    "backgroundColor": "#F5F7FA"
  },
  "permission": {
    "scope.camera": {
      "desc": "用于拍照记录错题和证书"
    },
    "scope.writePhotosAlbum": {
      "desc": "用于保存金句分享图片到相册"
    }
  },
  "requiredPrivateInfos": [
    "chooseImage",
    "chooseMedia"
  ]
}
```

### 微信订阅消息模板

```
需要申请的订阅消息模板:

1. 里程碑提醒模板
   模板名称: 考试提醒
   关键词: 考试名称 + 距离天数 + 提醒内容
   跳转页面: pages/milestones/action-card?id={milestone_id}&timing={timing}
   使用场景: 里程碑前15天/3天自动推送

2. 成绩进步提醒模板(可选)
   模板名称: 学习进展通知
   关键词: 科目 + 变化内容 + 建议
   跳转页面: pages/growth/add?type=progress&subject={subject_id}
   使用场景: 录入成绩后检测到进步时推送

订阅消息获取时机:
- Onboarding完成页: 引导用户订阅里程碑提醒
- 首次查看行动卡片时: 再次引导订阅
- 每月首次打开时: 检查订阅状态, 如未订阅则轻量提醒
```

### 桌面快捷方式

```
实现方式:
- 调用 wx.addToHomeScreen() (基础库 >= 2.30.0)
- 或引导用户手动添加:
  "点击右上角 ··· → 添加到桌面"

添加到桌面后的体验:
- 点击桌面图标直接打开小程序首页
- 首页顶部展示倒计时+今日金句(模拟小组件效果)
- Phase 4 原生App时才支持真正的iOS Widget/Android小组件
```

---

## 数据库初始化脚本要求（Seed Data）

```
初始化时需要预置的数据:

1. subjects表: 9条科目数据(见上方数据模型)

2. knowledge_nodes表: 
   - 9个科目 × 平均5个一级模块 × 平均18个二级章节 × 平均12个三级知识点
   - 总计约 9700 条记录
   - 数据来源: 上海高中教材目录 + 高考考纲
   - 初始版本可先建设6个高考科目(语数外+3个热门选考), 
     其余科目Phase 1.5补全
   - MVP最低要求: 数学、外语的知识点树完整到三级

3. milestones表: 
   - 约30-40个系统预置里程碑(2025-2026学年)
   - 包含高三完整时间线 + 高一高二通用节点
   - 需支持动态日期更新(is_dynamic_date=true的节点)

4. action_cards表:
   - 每个主要里程碑 × 2个时间点(15天/3天) = 约40-50张行动卡片
   - 每张卡片包含4-7个具体行动项

5. daily_quotes表:
   - 300+ 条金句
   - 按 category 和 applicable_phase 均匀分布
   - 确保每个 category 至少30条
   - MVP最低要求: 先准备100条覆盖所有类别

6. 上海16区数据:
   - districts参考数据(用于district字段的枚举值和显示名称)
   - 各区模考时间差异(Phase 1.5补全)
```

---

## 性能要求（Performance Requirements）

```
API响应时间:
- 首页Dashboard接口: < 500ms
- 列表查询接口: < 300ms
- 创建/更新接口: < 500ms
- 图片上传: < 3s (不含网络传输)
- 金句分享图片生成: < 2s

并发要求(Phase 1):
- 支持500 DAU
- 峰值QPS: 50

缓存策略:
- 知识点树: 全量缓存, 每日更新检查
- 系统里程碑: 全量缓存, 每日更新检查
- 行动卡片模板: 全量缓存
- 每日金句: 按用户缓存当天金句
- Dashboard数据: 按用户缓存, TTL=5分钟

数据库索引:
- 所有外键字段建立索引
- 高频查询字段建立复合索引(见各表定义中的INDEX说明)
```

---

## 安全要求（Security Requirements）

```
认证与授权:
- 所有API(除wx-login外)必须携带有效JWT token
- JWT有效期: 7天, 支持续期
- 用户只能访问自己创建的学生档案及相关数据
- API层校验: student.user_id === current_user.id

数据隐私:
- 所有用户数据加密存储(AES-256)
- 图片使用带签名的临时URL, 不公开访问
- 不收集用户地理位置、通讯录等无关权限
- 用户可在"我的"页面一键导出所有数据(JSON格式)
- 用户可在"我的"页面一键删除所有数据(含对象存储图片)
- 删除账户后数据保留30天(防误操作), 30天后彻底删除

隐私承诺(必须在以下3处展示):
1. 首页底部固定文字: "本产品不推荐任何培训课程或教师"
2. 付费页明确声明: "所有收入来自用户订阅，无任何课程导流分成"
3. 隐私政策页: 完整的数据使用说明

输入校验:
- 所有用户输入做XSS过滤
- SQL参数化查询(防注入)
- 文件上传类型白名单: jpg, jpeg, png
- 文件大小上限: 10MB
- 文本字段长度限制(见各表定义)
```

---

## 测试要求（Testing Requirements）

```
单元测试(必须覆盖):
- 金句分配算法(阶段感知、不重复、全部展示后循环)
- 里程碑筛选逻辑(年级/选科/区/外语一考)
- 成绩进步检测算法(得分率计算、跨考试对比、阈值判断)
- 付费权限校验(各功能的免费/标准/高级版访问控制)
- 满分自定义计算(得分率 = score/max_score * 100)
- 科目展示逻辑(高一9科 vs 高二高三6科)

集成测试(必须覆盖):
- 完整Onboarding流程(高一/高二未选科/高二已选科/高三)
- 错题录入→列表→详情→删除 完整流程
- 成绩录入→进步检测→成长记录自动生成 完整流程
- 里程碑提醒发送→打开→行动项勾选 完整流程
- 免费版容量限制→触达上限→升级弹窗 完整流程
- 多孩家庭: 切换孩子后数据隔离验证

E2E测试(关键路径):
- 新用户注册→Onboarding→首页展示→添加桌面
- 每日金句展示→收藏→分享图片生成
- 里程碑前15天提醒触发→查看行动卡片→勾选行动项
```

---

## 部署与环境配置（Deployment）

```
环境:
- dev:  开发环境, 本地数据库, mock微信登录
- staging: 预发布环境, 独立数据库, 微信测试号
- prod: 生产环境, 主数据库, 微信正式小程序

环境变量:
- DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
- COS_BUCKET, COS_REGION, COS_SECRET_ID, COS_SECRET_KEY
- WX_APP_ID, WX_APP_SECRET
- JWT_SECRET, JWT_EXPIRES_IN
- WECHAT_PAY_MCH_ID, WECHAT_PAY_API_KEY (付费功能)

CI/CD:
- 代码推送到 main 分支自动触发:
  1. 运行单元测试
  2. 运行集成测试
  3. 构建后端Docker镜像
  4. 部署到staging环境
  5. 手动确认后部署到prod

数据库迁移:
- 使用迁移工具(如 Prisma Migrate / Alembic / Knex Migrate)
- 每次schema变更必须有对应的迁移文件
- 生产环境迁移前必须备份
```

---

## MVP Phase 1 开发范围（Phase 1 Scope）

```
Phase 1 目标: 0-2个月内上线, 全部免费, 验证核心价值

Phase 1 包含:
✅ 微信登录
✅ Onboarding完整流程(年级选择/选科/区选择)
✅ 首页(倒计时+金句+里程碑摘要+功能入口)
✅ 每日金句(基础库50条)
✅ 里程碑时间线浏览(系统预置节点)
✅ 自定义里程碑(添加/编辑/删除)
✅ 知识点树浏览(2级)
✅ 成绩录入(含满分自定义, 限3次)
✅ 个人中心(孩子档案管理/隐私政策/关于)
✅ 多孩支持(创建多个学生档案)

Phase 1 不包含:
❌ 里程碑行动卡片(Phase 2)
❌ 完整金句库300条(Phase 2)
❌ 金句收藏/分享(Phase 2)
❌ 知识点3级展开(Phase 2)
❌ 错题本(Phase 1.5)
❌ 成长记录(Phase 1.5)
❌ 成绩趋势图(Phase 2)
❌ 桌面快捷方式引导(Phase 2)
❌ 学校进度记录(Phase 2)
❌ 付费系统(Phase 2)
❌ AI功能(Phase 3)

Phase 1 验证指标(Go/No-Go):
- Onboarding完成率 > 80%
- 7天留存率 > 35%
- 金句查看率 > 50%(每天至少看一次)
- 里程碑页面访问率 > 40%
- 任一指标未达标: 暂停开发, 重新评估核心假设
```

---

## Phase 1.5 开发范围（Phase 1.5 Scope）

```
Phase 1.5 目标: Phase 1上线后1-2个月, 新增错题本和成长记录, 仍全免费(有容量限制)

Phase 1.5 包含:
✅ 错题拍照录入(限10道)
✅ 错题列表/详情/筛选/删除
✅ 错题统计(首页摘要)
✅ 成长记录(限5条)
✅ 成长记录时间线视图
✅ 成绩进步自动检测 → 提示记录到成长册

Phase 1.5 验证指标:
- 错题本使用率 > 40%(至少录入1道)
- 成长记录使用率 > 30%(至少记录1条)
- 错题触达上限率 > 20%(达到10道免费上限)
```

---

## Phase 2 开发范围（Phase 2 Scope）

```
Phase 2 目标: Phase 1.5后2-3个月, 完善功能 + 推出付费

Phase 2 包含:
✅ 微信支付集成
✅ 订阅管理(免费/标准/高级, 月付/年付/全程包)
✅ 7天免费试用标准版
✅ 付费转化弹窗(各触发节点)
✅ 里程碑行动卡片(前15天/前3天)
✅ 微信订阅消息推送
✅ 完整金句库(300+条)
✅ 金句收藏 + 分享图片生成
✅ 知识点树3级展开(标准版)
✅ 错题本/成长记录无限存储(标准版)
✅ 成绩趋势分析图(标准版)
✅ 成长档案导出PDF/长图(标准版)
✅ 学校复习进度记录 + 联动(标准版)
✅ 桌面快捷方式引导(标准版)

Phase 2 验证指标:
- 30天留存率 > 40%
- 免费→标准版转化率 > 5%
- 全程包占付费用户 > 35%
- NPS > 40
```

---

## 附录A: 上海16区编码

```
| 编码       | 中文名   | 拼音        |
|-----------|---------|------------|
| huangpu   | 黄浦区   | Huangpu    |
| xuhui     | 徐汇区   | Xuhui      |
| changning | 长宁区   | Changning  |
| jingan    | 静安区   | Jing'an    |
| putuo     | 普陀区   | Putuo      |
| hongkou   | 虹口区   | Hongkou    |
| yangpu    | 杨浦区   | Yangpu     |
| minhang   | 闵行区   | Minhang    |
| baoshan   | 宝山区   | Baoshan    |
| jiading   | 嘉定区   | Jiading    |
| pudong    | 浦东新区  | Pudong     |
| jinshan   | 金山区   | Jinshan    |
| songjiang | 松江区   | Songjiang  |
| qingpu    | 青浦区   | Qingpu     |
| fengxian  | 奉贤区   | Fengxian   |
| chongming | 崇明区   | Chongming  |
```

---

## 附录B: 金句样例数据（前20条）

```json
[
  {"content": "所有的努力，终将不被辜负。", "category": "daily_encouragement", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "all"},
  {"content": "每天进步一点点，就是最好的节奏。", "category": "study_method", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "normal"},
  {"content": "不怕慢，就怕站。坚持就是胜利。", "category": "daily_encouragement", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "all"},
  {"content": "你已经准备了这么久，相信自己的积累。", "category": "pre_exam_motivation", "applicable_grades": ["gao2","gao3"], "applicable_phase": "pre_exam_30d"},
  {"content": "偶尔休息不是偷懒，是为了走更远的路。", "category": "stress_relief", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "pre_exam_7d"},
  {"content": "无论结果如何，你的努力本身就是最好的答案。", "category": "post_exam_relief", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "post_exam"},
  {"content": "孩子，不管分数多少，你永远是我们的骄傲。", "category": "parent_child_warmth", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "all"},
  {"content": "天生我材必有用。", "author": "李白", "category": "famous_quotes", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "all"},
  {"content": "高一是种子，高二是浇灌，高三是收获。现在种下的每一颗种子都算数。", "category": "gao1_special", "applicable_grades": ["gao1"], "applicable_phase": "all"},
  {"content": "基础打得牢，未来走得远。", "category": "gao1_special", "applicable_grades": ["gao1"], "applicable_phase": "all"},
  {"content": "每一道错题，都是通往正确答案的阶梯。", "category": "study_method", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "normal"},
  {"content": "学习不是百米冲刺，而是马拉松。保持节奏最重要。", "category": "daily_encouragement", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "all"},
  {"content": "你不需要懂物理化学历史，你只需要让孩子知道：家里一切都准备好了。", "category": "parent_child_warmth", "applicable_grades": ["gao3"], "applicable_phase": "pre_exam_30d"},
  {"content": "十年磨剑，今朝试锋。不问结果，只问是否全力以赴。", "category": "pre_exam_motivation", "applicable_grades": ["gao3"], "applicable_phase": "pre_exam_7d"},
  {"content": "你的平静就是孩子最大的力量。", "category": "parent_child_warmth", "applicable_grades": ["gao3"], "applicable_phase": "pre_exam_7d"},
  {"content": "进步不是直线，是螺旋上升。每次波动都是成长的一部分。", "category": "daily_encouragement", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "all"},
  {"content": "每一份付出，都在为未来的自己写推荐信。", "category": "daily_encouragement", "applicable_grades": ["gao2","gao3"], "applicable_phase": "normal"},
  {"content": "最暗的夜，才能看到最亮的星。", "category": "stress_relief", "applicable_grades": ["gao2","gao3"], "applicable_phase": "pre_exam_7d"},
  {"content": "三年陪伴，每一天都算数。", "category": "parent_child_warmth", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "all"},
  {"content": "博学之，审问之，慎思之，明辨之，笃行之。", "author": "《中庸》", "category": "famous_quotes", "applicable_grades": ["gao1","gao2","gao3"], "applicable_phase": "all"}
]
```

---

## 附录C: 行动卡片样例数据

```json
[
  {
    "milestone_category": "level_exam",
    "timing": "15d_before",
    "title": "等级考准备清单",
    "action_items": [
      {"icon": "🖨️", "text": "帮孩子打印各科核心公式/要点汇总表", "detail": "可在知识点树中查看各科章节", "category": "print"},
      {"icon": "🚗", "text": "确认考试地点和交通路线", "category": "transport"},
      {"icon": "💬", "text": "和孩子聊一下：三科中哪科最想冲刺？", "category": "communication"},
      {"icon": "😴", "text": "开始调整作息，保证每晚11点前入睡", "category": "sleep"},
      {"icon": "✏️", "text": "准备好2B铅笔、黑色签字笔、橡皮等文具（备两套）", "category": "purchase"},
      {"icon": "📸", "text": "翻一下错题本，看看哪科积累最多", "detail": "重点打印错题多的章节资料", "category": "errornote"}
    ],
    "footer_tip": "跟着学校节奏走即可，不需要额外加压",
    "quote_category": "pre_exam_motivation",
    "applicable_grades": ["gao3"]
  },
  {
    "milestone_category": "level_exam",
    "timing": "3d_before",
    "title": "等级考最后检查",
    "action_items": [
      {"icon": "📋", "text": "检查准考证、身份证（拍照备份一份）", "category": "document"},
      {"icon": "🚗", "text": "再确认一遍考场地址和出发时间", "category": "transport"},
      {"icon": "✏️", "text": "检查文具是否齐全（备两套）", "category": "purchase"},
      {"icon": "🍎", "text": "饮食清淡，不要尝试新餐厅", "category": "diet"},
      {"icon": "💬", "text": "不再讨论分数和目标，只聊轻松的话题", "category": "communication"},
      {"icon": "😴", "text": "晚上10:30开始关灯，营造安静环境", "category": "sleep"}
    ],
    "footer_tip": "最重要的：你的平静就是孩子最大的力量",
    "quote_category": "stress_relief",
    "applicable_grades": ["gao3"]
  },
  {
    "milestone_category": "autumn_exam",
    "timing": "15d_before",
    "title": "高考准备清单",
    "action_items": [
      {"icon": "🖨️", "text": "帮孩子打印语数外核心公式/知识要点速查表", "category": "print"},
      {"icon": "🚗", "text": "确认三天考试的考场地址（可能不同）", "category": "transport"},
      {"icon": "😴", "text": "调整作息，目标每晚10:30入睡", "category": "sleep"},
      {"icon": "🛒", "text": "采购考试文具（2B铅笔、签字笔、橡皮、尺子，各备两套）", "category": "purchase"},
      {"icon": "📸", "text": "最后翻一遍错题本，重点看高频错题章节", "category": "errornote"},
      {"icon": "🍎", "text": "规划考试三天的饮食，清淡为主", "category": "diet"},
      {"icon": "💬", "text": "减少讨论分数和目标，多表达支持和信心", "category": "communication"}
    ],
    "footer_tip": "你已经陪伴孩子走过了最艰难的路，最后15天，做好后勤就是最大的贡献",
    "quote_category": "pre_exam_motivation",
    "applicable_grades": ["gao3"]
  },
  {
    "milestone_category": "autumn_exam",
    "timing": "3d_before",
    "title": "高考最后准备",
    "action_items": [
      {"icon": "📋", "text": "检查准考证、身份证（拍照备份一份到手机）", "category": "document"},
      {"icon": "🚗", "text": "提前走一遍6月7日考场路线，预估通勤时间", "category": "transport"},
      {"icon": "✏️", "text": "最终检查文具：2B铅笔、黑色签字笔、橡皮、直尺（各两套）", "category": "purchase"},
      {"icon": "🍎", "text": "今天起饮食清淡，不吃生冷、辛辣，不尝试新食物", "category": "diet"},
      {"icon": "💬", "text": "不再讨论任何考试相关话题，陪孩子做轻松的事", "category": "communication"},
      {"icon": "😴", "text": "10:00关灯，营造安静环境，即使睡不着也不焦虑", "category": "sleep"},
      {"icon": "📱", "text": "设好闹钟（至少两个），确保明天按时起床", "category": "document"}
    ],
    "footer_tip": "最重要的：你的平静就是孩子最大的力量。高考只是一场考试，不是人生的终点。",
    "quote_category": "stress_relief",
    "applicable_grades": ["gao3"]
  },
  {
    "milestone_category": "spring_exam",
    "timing": "15d_before",
    "title": "春季高考（含外语一考）准备清单",
    "action_items": [
      {"icon": "🖨️", "text": "帮孩子打印英语高频词汇/短语速查表", "category": "print"},
      {"icon": "📋", "text": "确认听说测试设备要求（是否需自带耳机等）", "category": "document"},
      {"icon": "💬", "text": "提醒孩子：这次考好了6月少一门压力，一般也没关系6月还有一次", "category": "communication"},
      {"icon": "✏️", "text": "准备好考试文具和证件", "category": "purchase"},
      {"icon": "😴", "text": "调整作息，保证充足睡眠", "category": "sleep"}
    ],
    "footer_tip": "上海外语一年两考取最高分，1月这次是"多一次机会"，心态放松",
    "quote_category": "pre_exam_motivation",
    "applicable_grades": ["gao3"]
  },
  {
    "milestone_category": "school_exam",
    "timing": "15d_before",
    "title": "期末考试准备清单",
    "action_items": [
      {"icon": "📸", "text": "翻一下孩子的错题本，看看哪科错题最多", "category": "errornote"},
      {"icon": "🖨️", "text": "帮孩子整理各科笔记和试卷", "category": "print"},
      {"icon": "😴", "text": "保障作息规律，不要临时熬夜", "category": "sleep"},
      {"icon": "💬", "text": "问一下孩子哪科最需要帮忙整理资料", "category": "communication"}
    ],
    "footer_tip": "高一是打基础的关键期，成绩波动很正常，重要的是学习习惯",
    "quote_category": "daily_encouragement",
    "applicable_grades": ["gao1", "gao2"]
  },
  {
    "milestone_category": "registration",
    "timing": "15d_before",
    "title": "高考报名提醒",
    "action_items": [
      {"icon": "📋", "text": "确认高考报名时间和方式（通常通过学校统一组织）", "category": "document"},
      {"icon": "📋", "text": "准备好报名所需材料（身份证、户口本等）", "category": "document"},
      {"icon": "💬", "text": "和孩子确认选考科目是否最终确定", "category": "communication"},
      {"icon": "📷", "text": "准备好报名用的证件照（如学校要求）", "category": "document"}
    ],
    "footer_tip": "报名通常由学校统一组织，关注学校通知即可",
    "quote_category": "daily_encouragement",
    "applicable_grades": ["gao3"]
  },
  {
    "milestone_category": "comprehensive_eval",
    "timing": "15d_before",
    "title": "综合评价报名准备",
    "action_items": [
      {"icon": "📋", "text": "查看目标院校的综评报名要求和截止时间", "category": "document"},
      {"icon": "🏆", "text": "整理孩子的获奖证书、荣誉证明（可在成长记录中查看）", "detail": "点击查看孩子的成长记录", "category": "document"},
      {"icon": "📝", "text": "准备个人陈述/自荐信材料", "category": "document"},
      {"icon": "💬", "text": "和孩子讨论综评目标院校和专业", "category": "communication"}
    ],
    "footer_tip": "综合评价是额外机会，准备好材料但不要给孩子增加额外压力",
    "quote_category": "daily_encouragement",
    "applicable_grades": ["gao3"]
  }
]
```

---

## 附录D: 文件结构建议

```
project-root/
├── miniprogram/                    # 微信小程序前端
│   ├── app.js
│   ├── app.json
│   ├── app.wxss
│   ├── assets/                     # 静态资源(TabBar图标等)
│   ├── components/                 # 公共组件
│   │   ├── countdown-card/         # 倒计时卡片组件
│   │   ├── quote-card/             # 金句卡片组件
│   │   ├── action-item/            # 行动项(可勾选)组件
│   │   ├── subject-picker/         # 科目选择器组件
│   │   ├── knowledge-tree/         # 知识点树组件(可折叠)
│   │   ├── student-switcher/       # 孩子切换器组件
│   │   ├── upgrade-modal/          # 升级引导弹窗组件
│   │   ├── empty-state/            # 空状态占位组件
│   │   └── image-viewer/           # 图片查看器组件
│   ├── pages/                      # 页面(见页面列表)
│   │   ├── index/
│   │   ├── onboarding/
│   │   ├── milestones/
│   │   ├── knowledge/
│   │   ├── exams/
│   │   ├── errors/
│   │   ├── growth/
│   │   ├── quotes/
│   │   └── profile/
│   ├── services/                   # API调用封装
│   │   ├── api.js                  # 基础HTTP请求封装(含token处理)
│   │   ├── auth.js                 # 认证相关
│   │   ├── student.js              # 学生档案API
│   │   ├── milestone.js            # 里程碑API
│   │   ├── quote.js                # 金句API
│   │   ├── exam.js                 # 成绩API
│   │   ├── errorNote.js            # 错题本API
│   │   ├── growth.js               # 成长记录API
│   │   ├── schoolProgress.js       # 学校进度API
│   │   └── subscription.js         # 订阅管理API
│   ├── utils/                      # 工具函数
│   │   ├── date.js                 # 日期计算(倒计时等)
│   │   ├── image.js                # 图片压缩/上传
│   │   ├── permission.js           # 付费权限检查
│   │   └── storage.js              # 本地缓存管理
│   └── constants/                  # 常量定义
│       ├── subjects.js             # 科目列表
│       ├── districts.js            # 16区列表
│       ├── errorTypes.js           # 错误类型枚举
│       └── plans.js                # 付费方案定义
│
├── server/                         # 后端服务
│   ├── src/
│   │   ├── app.js                  # 应用入口
│   │   ├── config/                 # 配置
│   │   │   ├── database.js
│   │   │   ├── cos.js              # 对象存储配置
│   │   │   └── wechat.js           # 微信配置
│   │   ├── middleware/             # 中间件
│   │   │   ├── auth.js             # JWT认证
│   │   │   ├── permission.js       # 付费权限检查
│   │   │   ├── errorHandler.js     # 统一错误处理
│   │   │   └── rateLimiter.js      # 频率限制
│   │   ├── routes/                 # 路由
│   │   │   ├── auth.js
│   │   │   ├── students.js
│   │   │   ├── milestones.js
│   │   │   ├── quotes.js
│   │   │   ├── exams.js
│   │   │   ├── errorNotes.js
│   │   │   ├── growthRecords.js
│   │   │   ├── schoolProgress.js
│   │   │   ├── subscription.js
│   │   │   └── upload.js
│   │   ├── models/                 # 数据模型(ORM)
│   │   ├── services/               # 业务逻辑
│   │   │   ├── quoteService.js     # 金句分配算法
│   │   │   ├── milestoneService.js # 里程碑筛选/提醒逻辑
│   │   │   ├── progressDetector.js # 成绩进步检测
│   │   │   ├── imageService.js     # 图片处理
│   │   │   └── paymentService.js   # 支付处理
│   │   ├── jobs/                   # 定时任务
│   │   │   ├── dailyQuoteJob.js    # 每日金句分配
│   │   │   ├── reminderJob.js      # 里程碑提醒
│   │   │   └── cleanupJob.js       # 图片清理
│   │   └── utils/
│   ├── migrations/                 # 数据库迁移文件
│   ├── seeders/                    # 种子数据
│   │   ├── subjects.js
│   │   ├── knowledgeTree.js
│   │   ├── milestones.js
│   │   ├── actionCards.js
│   │   └── quotes.js
│   └── tests/                      # 测试
│       ├── unit/
│       └── integration/
│
├── docs/
│   ├── product-vision-v5.1.md     # 产品愿景文档
│   └── spec.md                     # 本文件
│
├── .env.example                    # 环境变量模板
├── docker-compose.yml              # 本地开发环境
├── Dockerfile                      # 后端Docker构建
└── README.md
```

---

## 附录E: 关键业务规则汇总

```
1. 科目展示规则
   - 高一(未选科): 展示全部9科
   - 高二(已选科): 展示3必考 + 3选考 = 6科
   - 高二(未选科): 展示全部9科
   - 高三: 必须已选科, 展示6科

2. 满分默认值规则
   - 首次录入: 大三门默认150, 小三门默认100
   - 非首次录入: 沿用该科目上次使用的满分值
   - 用户可手动修改, 范围10-300

3. 金句不重复规则
   - 同一个student, 同一条金句在展示过后不再展示
   - 所有适用金句全部展示过一轮后, 清空历史重新循环
   - 每天8:00分配, 当天内不变

4. 里程碑适用性筛选规则(AND逻辑)
   - applicable_grades 包含当前学生年级
   - AND applicable_subjects 为NULL 或 与学生选科有交集
   - AND applicable_districts 为NULL 或 包含学生所在区
   - AND (requires_jan_english=false 或 学生has_jan_english_exam=true)

5. 成绩进步检测规则
   - 对比范围: 同一exam_type的前一次考试
   - 阈值: 同科目得分率提升 >= 10个百分点
   - 触发: 录入成绩API返回时, 在response中附带progress_detected

6. 免费版容量限制
   - 错题: 10道(含所有科目)
   - 成长记录: 5条
   - 考试记录: 3次(不限科目数)
   - 达到上限时API返回403 + 特定错误码

7. 图片存储规则
   - 上传时压缩: 最大宽度1200px, 质量80%, JPEG格式
   - 临时URL有效期: 2小时
   - 用户删除记录时同步删除图片
   - 孤立图片(上传但未关联)24小时后清理

8. 多孩家庭规则
   - 一个user可创建多个student
   - 所有数据按student_id隔离
   - 前端使用student-switcher组件切换
   - 付费状态绑定在user级别(一个订阅覆盖所有孩子)

9. 行动卡片勾选持久化
   - 勾选状态存储在 milestone_reminders.action_items_checked
   - 以action_item在数组中的索引记录
   - 所有项勾选完成时前端展示"准备就绪"状态
```

---

*End of spec.md*
```

---

以上就是 `spec.md` 的完整内容。整个文档涵盖了：

1. **数据模型** — 16张表的完整定义
2. **API设计** — 所有 RESTful 端点（含请求/响应格式）
3. **页面结构** — 25个页面 + 交互规范
4. **功能权限矩阵** — 免费/标准/高级版功能对照
5. **定时任务** — 金句分配、里程碑提醒、图片清理
6. **错误处理** — 完整错误码定义
7. **图片处理** — 上传/压缩/存储/安全规范
8. **微信小程序配置** — app.json、订阅消息、桌面快捷方式
9. **测试要求** — 单元/集成/E2E测试范围
10. **部署配置** — 环境变量、CI/CD流程
11. **Phase 1/1.5/2 开发范围** — 明确的分期交付边界
12. **附录** — 区编码、金句样例、行动卡片样例、文件结构、业务规则汇总
