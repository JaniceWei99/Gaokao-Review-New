# Development Plan - 高考家长帮 v5.1

> **文档版本**: 1.0
> **对应 Spec 版本**: v5.1
> **开发模式**: 1人独立全栈开发
> **预计总工期**: 20 周（Phase 0-2），Phase 3-4 视验证结果决定
> **详细程度**: 可执行级（含 Sprint 拆分、估时、技术实现要点）

---

## 目录

1. [Architecture — 系统架构](#1-architecture--系统架构)
2. [Workflow — 开发工作流](#2-workflow--开发工作流)
3. [Phase 0 — 基础设施搭建](#3-phase-0--基础设施搭建week-1-2)
4. [Phase 1 — 核心 MVP](#4-phase-1--核心-mvpweek-3-8)
5. [Phase 1.5 — 错题本 + 成长记录](#5-phase-15--错题本--成长记录week-9-12)
6. [Phase 2 — 付费变现 + 完整功能](#6-phase-2--付费变现--完整功能week-13-20)
7. [Phase 3 — AI 增值功能](#7-phase-3--ai-增值功能week-21-28)
8. [Phase 4 — 跨地区扩展](#8-phase-4--跨地区扩展week-29)
9. [风险应对](#9-风险应对)
10. [附录 — 关键技术实现参考](#10-附录--关键技术实现参考)

---

## 1. Architecture — 系统架构

### 1.1 系统架构总览

```
                    ┌─────────────────────────────┐
                    │    WeChat Mini Program        │
                    │    (WXML / WXSS / JS)         │
                    │    ── 前端 ──                  │
                    └──────────┬──────────────────┘
                               │ HTTPS (RESTful JSON)
                               ▼
                    ┌─────────────────────────────┐
                    │    Nginx                      │
                    │    (反向代理 + SSL + 静态资源)  │
                    └──────────┬──────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Application                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │
│  │  API Routes │  │  Services  │  │  APScheduler       │ │
│  │  (Routers)  │  │  (业务逻辑) │  │  (定时任务:        │ │
│  │             │  │            │  │   金句分配/提醒)    │ │
│  └──────┬─────┘  └──────┬─────┘  └────────────────────┘ │
│         │               │                                 │
│  ┌──────┴───────────────┴──────────┐                     │
│  │         SQLAlchemy ORM           │                     │
│  └──────────────┬──────────────────┘                     │
└─────────────────┼────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│  PostgreSQL   │    │ Tencent COS  │
│  (结构化数据)  │    │ (图片存储)    │
└──────────────┘    └──────────────┘

Phase 2+ 新增:
┌──────────────┐
│    Redis      │  ← 缓存 Dashboard / Rate Limiting / Session
└──────────────┘
```

### 1.2 技术栈选型与理由

#### 后端：Python FastAPI

| 对比维度 | FastAPI | Node.js + NestJS | Node.js + Express |
|---------|---------|-------------------|-------------------|
| **开发速度** | ★★★★★ Pydantic 自动校验，少写 50% 样板代码 | ★★★ 装饰器+DI 体系学习曲线陡 | ★★★★ 灵活但无约束 |
| **API 文档** | ★★★★★ 自动生成 Swagger/ReDoc | ★★★★ 需配置 | ★★★ 需额外库 |
| **AI 集成(Phase 3)** | ★★★★★ Python 是 AI 生态原生语言 | ★★ 需要跨语言调用或用 JS AI SDK | ★★ 同左 |
| **微信 SDK** | ★★★★ `wechatpy` 库成熟 | ★★★★★ 生态最丰富 | ★★★★★ 同左 |
| **单人维护成本** | ★★★★★ 代码量少，类型提示清晰 | ★★★ 文件多，概念重 | ★★★★ 灵活但易混乱 |
| **腾讯云适配** | ★★★★ Python SDK 完善 | ★★★★ Node SDK 完善 | ★★★★ 同左 |

**选择 FastAPI 的核心理由**：

1. **Phase 3 AI 集成是决定性因素** — AI 功能（金句生成、错题分类、成长报告）在 Python 生态中集成成本极低。如果用 Node.js，Phase 3 要么引入 Python 微服务（增加运维复杂度），要么用不成熟的 JS AI SDK
2. **单人开发效率** — FastAPI 的 Pydantic 模型同时充当请求校验、响应序列化和文档生成，一个 schema 解决三件事
3. **自动 API 文档** — 独立开发时不需要额外维护 Postman 集合，Swagger UI 开箱即用，方便前端联调
4. **前端是独立代码库** — 微信小程序用 WXML/WXSS/JS，后端用什么语言对前端无影响，没有"全栈 JS 一致性"的收益

> **风险缓解**：微信支付 Node.js 生态更成熟 → 方案：使用 `wechatpy` 库 + 腾讯云官方 Python SDK for WeChat Pay，Phase 2 开发前先做 spike 验证

#### 数据库：PostgreSQL

| 对比维度 | PostgreSQL | MySQL |
|---------|------------|-------|
| **JSON 支持** | ★★★★★ JSONB 可索引、可查询 | ★★★ JSON 类型不可索引 |
| **数组类型** | ★★★★★ 原生 ARRAY 类型 | ❌ 不支持 |
| **复杂查询** | ★★★★★ CTE、窗口函数完善 | ★★★★ 基本够用 |
| **全文检索** | ★★★★ 内置 tsvector | ★★★ 需额外配置 |
| **腾讯云支持** | ★★★★ TencentDB for PostgreSQL | ★★★★★ 最成熟 |

**选择 PostgreSQL 的核心理由**：

1. **JSONB 是刚需** — `milestones.applicable_grades`、`action_cards.action_items`、`milestone_reminders.action_items_checked` 等大量字段需要存储和查询 JSON 数组。PostgreSQL 的 JSONB 支持 GIN 索引，可以高效地做 `WHERE applicable_grades @> '["gao3"]'` 这样的查询
2. **里程碑筛选逻辑复杂** — 需要同时判断年级、选科、区、外语一考四个维度的交叉筛选，PostgreSQL 的数组操作符（`&&` 交集、`@>` 包含）比 MySQL 的 JSON_CONTAINS 更直观高效
3. **Alembic 迁移工具对 PostgreSQL 支持最好** — 包括 ARRAY、JSONB 类型的迁移

#### ORM：SQLAlchemy 2.0 + Alembic

**理由**：
- SQLAlchemy 2.0 支持 async（配合 FastAPI 的 async 特性）
- Alembic 是 Python 生态最成熟的数据库迁移工具
- 对 PostgreSQL 的 JSONB、ARRAY 类型有原生支持
- 类型提示支持好，配合 IDE 开发体验佳

#### 定时任务：APScheduler（Phase 1-1.5）→ Celery + Redis（Phase 2+）

**Phase 1-1.5 用 APScheduler**：
- 内嵌在 FastAPI 进程中，无需额外部署
- 两个定时任务（金句分配 08:00、提醒检查 09:00）足够轻量
- 单进程足以应对 Phase 1 的 500 DAU

**Phase 2+ 升级 Celery + Redis**：
- 付费后用户量增长，需要可靠的任务队列
- 图片处理、PDF 生成等耗时任务需要异步处理
- Redis 同时承担缓存（Dashboard 数据 TTL=5min）和 Rate Limiting

#### 缓存：无（Phase 1）→ Redis（Phase 2+）

**Phase 1 不用 Redis 的理由**：
- 500 DAU + 峰值 50 QPS，PostgreSQL 裸查足以应对
- 知识点树和里程碑数据可以用 FastAPI 的内存 lru_cache 缓存
- 减少运维复杂度（一人开发，少一个服务少一个故障点）

**Phase 2 引入 Redis**：
- Dashboard 聚合接口需要缓存（避免每次查 5+ 张表）
- 微信支付回调需要幂等性校验（Redis SETNX）
- 订阅消息频率控制

#### 部署：腾讯云

| 服务 | 产品 | 规格(Phase 1) | 预估月费 |
|------|------|--------------|---------|
| 计算 | 轻量应用服务器 | 2C4G | ~¥50/月 |
| 数据库 | TencentDB PostgreSQL | 1C2G 20GB | ~¥60/月 |
| 对象存储 | COS | 标准存储 | ~¥5/月(按量) |
| CDN | 腾讯云 CDN | 用于图片加速 | ~¥5/月(按量) |
| SSL | 免费 SSL | Let's Encrypt | ¥0 |
| **合计** | | | **~¥120/月** |

**选择腾讯云的理由**：微信小程序后端调用微信 API（登录、支付、订阅消息）时，腾讯云服务器的网络延迟最低。腾讯云 COS 也是微信小程序图片上传的官方推荐方案。

### 1.3 项目目录结构

```
gaokao-companion/
├── miniprogram/                         # ── 微信小程序前端 ──
│   ├── app.js                           # 全局入口
│   ├── app.json                         # 页面路由 + TabBar 配置
│   ├── app.wxss                         # 全局样式
│   ├── assets/                          # 静态资源（图标、TabBar 图片）
│   ├── components/                      # 公共组件
│   │   ├── countdown-card/              # 倒计时卡片
│   │   ├── quote-card/                  # 金句卡片（含收藏/分享按钮）
│   │   ├── action-item/                 # 行动项（可勾选）
│   │   ├── subject-picker/              # 科目选择器
│   │   ├── knowledge-tree/              # 知识点树（可折叠）
│   │   ├── student-switcher/            # 多孩切换
│   │   ├── upgrade-modal/               # 升级引导弹窗
│   │   ├── empty-state/                 # 空状态占位
│   │   └── image-viewer/                # 图片查看器
│   ├── pages/                           # 页面目录（25 个页面）
│   │   ├── index/                       # 首页
│   │   ├── onboarding/                  # 引导流程（6 页）
│   │   ├── milestones/                  # 里程碑（3 页）
│   │   ├── knowledge/                   # 知识点浏览
│   │   ├── exams/                       # 成绩管理（3 页）
│   │   ├── errors/                      # 错题本（3 页）
│   │   ├── growth/                      # 成长记录（3 页）
│   │   ├── quotes/                      # 金句收藏
│   │   └── profile/                     # 个人中心（4 页）
│   ├── services/                        # API 调用封装
│   │   ├── api.js                       # HTTP 基础封装（含 token 自动注入）
│   │   ├── auth.js
│   │   ├── student.js
│   │   ├── milestone.js
│   │   ├── quote.js
│   │   ├── exam.js
│   │   ├── errorNote.js
│   │   ├── growth.js
│   │   └── subscription.js
│   ├── utils/                           # 工具函数
│   │   ├── date.js                      # 日期计算、倒计时
│   │   ├── image.js                     # 图片压缩
│   │   ├── permission.js                # 付费权限校验
│   │   └── storage.js                   # 本地缓存
│   └── constants/                       # 常量
│       ├── subjects.js
│       ├── districts.js
│       └── plans.js
│
├── server/                              # ── FastAPI 后端 ──
│   ├── app/
│   │   ├── main.py                      # FastAPI 入口 + 生命周期管理
│   │   ├── config.py                    # Settings（pydantic-settings）
│   │   ├── database.py                  # async SQLAlchemy 引擎 + session
│   │   ├── models/                      # SQLAlchemy ORM 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py                  # User
│   │   │   ├── student.py               # Student
│   │   │   ├── subject.py               # Subject
│   │   │   ├── knowledge.py             # KnowledgeNode
│   │   │   ├── milestone.py             # Milestone, MilestoneReminder
│   │   │   ├── action_card.py           # ActionCard
│   │   │   ├── quote.py                 # DailyQuote, UserQuoteFavorite, UserQuoteHistory
│   │   │   ├── exam.py                  # Exam, ExamScore
│   │   │   ├── error_note.py            # ErrorNote
│   │   │   ├── growth_record.py         # GrowthRecord
│   │   │   ├── school_progress.py       # SchoolProgress
│   │   │   └── subscription.py          # UserSubscription
│   │   ├── schemas/                     # Pydantic 请求/响应 Schema
│   │   │   ├── auth.py
│   │   │   ├── student.py
│   │   │   ├── milestone.py
│   │   │   ├── quote.py
│   │   │   ├── exam.py
│   │   │   ├── error_note.py
│   │   │   ├── growth_record.py
│   │   │   └── subscription.py
│   │   ├── routers/                     # API 路由
│   │   │   ├── auth.py                  # POST /api/auth/wx-login
│   │   │   ├── students.py              # CRUD /api/students
│   │   │   ├── milestones.py            # /api/students/:id/milestones
│   │   │   ├── quotes.py               # /api/students/:id/quote
│   │   │   ├── exams.py                # /api/students/:id/exams
│   │   │   ├── error_notes.py          # /api/students/:id/error-notes
│   │   │   ├── growth_records.py       # /api/students/:id/growth-records
│   │   │   ├── school_progress.py      # /api/students/:id/school-progress
│   │   │   ├── subscription.py         # /api/subscription
│   │   │   ├── upload.py               # /api/upload/image
│   │   │   └── dashboard.py            # /api/students/:id/dashboard
│   │   ├── services/                    # 业务逻辑层
│   │   │   ├── auth_service.py          # 微信登录 + JWT
│   │   │   ├── quote_service.py         # 金句分配算法
│   │   │   ├── milestone_service.py     # 里程碑筛选 + 提醒逻辑
│   │   │   ├── progress_detector.py     # 成绩进步检测
│   │   │   ├── image_service.py         # COS 上传/签名 URL
│   │   │   └── payment_service.py       # 微信支付（Phase 2）
│   │   ├── jobs/                        # 定时任务
│   │   │   ├── scheduler.py             # APScheduler 配置
│   │   │   ├── daily_quote_job.py       # 每日 08:00 金句分配
│   │   │   ├── reminder_job.py          # 每日 09:00 提醒检查
│   │   │   └── cleanup_job.py           # 每周日 03:00 图片清理
│   │   ├── middleware/
│   │   │   ├── auth.py                  # JWT 解析 + 用户注入
│   │   │   ├── permission.py            # 付费权限检查依赖
│   │   │   └── error_handler.py         # 全局异常处理
│   │   └── utils/
│   │       ├── wechat.py                # 微信 API 工具（code2session 等）
│   │       └── date_utils.py            # 日期/倒计时计算
│   ├── migrations/                      # Alembic 迁移
│   │   ├── env.py
│   │   └── versions/
│   ├── seeds/                           # 种子数据（JSON 格式）
│   │   ├── subjects.json
│   │   ├── knowledge_tree/              # 按科目拆分的知识点数据
│   │   │   ├── math.json
│   │   │   ├── chinese.json
│   │   │   └── ...
│   │   ├── milestones.json
│   │   ├── action_cards.json
│   │   └── quotes.json
│   ├── tests/
│   │   ├── conftest.py                  # pytest fixtures（测试数据库等）
│   │   ├── unit/
│   │   │   ├── test_quote_service.py
│   │   │   ├── test_milestone_service.py
│   │   │   ├── test_progress_detector.py
│   │   │   └── test_permission.py
│   │   └── integration/
│   │       ├── test_onboarding.py
│   │       ├── test_exam_flow.py
│   │       └── test_error_note_flow.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic.ini
│   └── seed.py                          # 种子数据导入脚本
│
├── docker-compose.yml                   # 本地开发环境（PG + App）
├── docker-compose.prod.yml              # 生产部署
├── .env.example                         # 环境变量模板
├── .github/
│   └── workflows/
│       └── ci.yml                       # GitHub Actions CI/CD
├── Makefile                             # 常用命令快捷入口
└── README.md
```

### 1.4 数据流图

#### 核心场景：首页加载

```
用户打开小程序
       │
       ▼
[前端] wx.login() → 获取 code
       │
       ▼
[前端] POST /api/auth/wx-login { code }
       │
       ▼
[后端] code → 微信 code2session → openid
       │ → 查/创建 User → 生成 JWT
       │
       ▼
[前端] 存储 JWT → GET /api/students/:id/dashboard
       │
       ▼
[后端] Dashboard 聚合查询（一次请求返回所有首页数据）
       │ ├── today_quote      ← quote_service（今日金句）
       │ ├── countdowns       ← milestone_service（倒计时）
       │ ├── active_action_card ← milestone_service（当前行动卡片）
       │ ├── upcoming_milestones ← milestone_service（近期里程碑）
       │ ├── error_notes_summary ← 错题统计
       │ ├── growth_records_count ← 成长记录数
       │ └── subscription     ← 当前订阅状态 + 功能权限
       │
       ▼
[前端] 渲染首页
```

#### 核心场景：错题拍照录入

```
[前端] 用户点击"拍照记录错题"
       │
       ▼
[前端] wx.chooseMedia() → 选择/拍摄图片
       │
       ▼
[前端] wx.compressImage() → 压缩到 1200px / 80%
       │
       ▼
[前端] POST /api/upload/image → 获取 COS 临时上传凭证
       │
       ▼
[前端] 直传图片到 COS → 获得 image_key
       │
       ▼
[前端] POST /api/students/:id/error-notes
       │ { subject_id, knowledge_node_id, error_type,
       │   source, note, question_image_key }
       │
       ▼
[后端] 校验付费权限（免费版 <= 10 道？）
       │ → 校验参数
       │ → 存储 ErrorNote 记录
       │ → 返回 error_note 对象
       │
       ▼
[前端] 跳转到错题列表页
```

---

## 2. Workflow — 开发工作流

### 2.1 Git 分支策略（Trunk-based，适合单人）

```
main ──────────────────────────────────────────────►
  │                                     ▲
  ├── feat/onboarding ─── ... ──── merge┘
  │                                     ▲
  ├── feat/daily-quote ── ... ──── merge┘
  │                                     ▲
  ├── fix/milestone-filter ... ──── merge┘
  │
  └── ...
```

**规则**：
- `main` 分支始终保持可部署状态
- 每个功能/修复从 `main` 拉 feature 分支
- 完成后直接合并回 `main`（单人无需 PR review，但跑 CI 通过后再合并）
- **分支命名**: `feat/xxx`、`fix/xxx`、`chore/xxx`
- **commit 格式**: `feat(module): description` / `fix(module): description`
- 每个 Sprint 结束时打 tag: `v0.1.0`、`v0.2.0` ...

### 2.2 每日开发循环

```
┌─ 开始 ────────────────────────────────────────┐
│                                                │
│  1. 拉取最新代码 (git pull)                     │
│  2. 查看今日 Sprint 任务清单                     │
│  3. 选择一个任务，创建 feature 分支              │
│  4. 编码：                                      │
│     ├── 写/更新 Pydantic Schema                 │
│     ├── 写/更新 SQLAlchemy Model                │
│     ├── 写 Service 业务逻辑                     │
│     ├── 写 Router 路由                          │
│     ├── 写单元测试（核心算法）                   │
│     └── 写前端页面 + 对接 API                    │
│  5. 本地运行测试 (make test)                     │
│  6. 合并到 main，推送                            │
│  7. CI 自动部署到 staging                        │
│  8. 在微信开发者工具中指向 staging 验证           │
│  9. 更新任务状态                                 │
│                                                │
└────────────────────────────────────────────────┘
```

### 2.3 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml 核心流程

触发条件: push to main / pull_request

Steps:
  1. Setup Python 3.11 + Node 18
  2. Install dependencies (pip + npm)
  3. Lint: ruff check + ruff format --check
  4. Type check: mypy (后端)
  5. Unit tests: pytest tests/unit/ --cov
  6. Integration tests: pytest tests/integration/ (需要 test DB)
  7. Build Docker image
  8. Deploy to staging (自动)
  9. Deploy to production (手动触发，需 tag)
```

### 2.4 本地开发环境

```bash
# 一键启动开发环境
docker-compose up -d  # 启动 PostgreSQL
make migrate          # 运行数据库迁移
make seed             # 导入种子数据
make dev              # 启动 FastAPI 开发服务器 (uvicorn --reload)
```

**Makefile 快捷命令**：

```makefile
dev:           uvicorn app.main:app --reload --port 8000
test:          pytest tests/ -v --tb=short
test-unit:     pytest tests/unit/ -v
test-cov:      pytest tests/ --cov=app --cov-report=html
migrate:       alembic upgrade head
migrate-new:   alembic revision --autogenerate -m "$(msg)"
seed:          python seed.py
lint:          ruff check app/ && ruff format --check app/
format:        ruff format app/
```

### 2.5 前后端联调方式

```
本地开发:
  ├── 后端: localhost:8000 (FastAPI + 自动文档 /docs)
  ├── 前端: 微信开发者工具 → project.config.json 指向 localhost:8000
  └── 数据库: Docker PostgreSQL localhost:5432

Staging:
  ├── 后端: staging-api.xxx.com
  ├── 前端: 微信开发者工具 → 体验版
  └── 数据库: 腾讯云 PostgreSQL (staging 实例)

Production:
  ├── 后端: api.xxx.com
  ├── 前端: 微信小程序正式版
  └── 数据库: 腾讯云 PostgreSQL (prod 实例)
```

### 2.6 代码质量保证

| 措施 | 工具 | 时机 |
|------|------|------|
| 代码格式化 | ruff format | 保存时（IDE 配置） |
| Lint | ruff check | pre-commit hook + CI |
| 类型检查 | mypy (strict) | CI |
| 单元测试 | pytest | CI + 本地 make test |
| 集成测试 | pytest + test DB | CI |
| 依赖安全 | pip-audit | 每周一次 |

---

## 3. Phase 0 — 基础设施搭建（Week 1-2）

### 目标
搭建完整的开发、测试、部署环境，完成数据库 Schema 设计和种子数据准备。Phase 0 结束时，任何一个 API 都可以快速开始编写。

### Sprint 0 任务清单

| # | 任务 | 估时 | 产出 |
|---|------|------|------|
| 0.1 | 初始化 FastAPI 项目骨架 | 2h | `server/` 目录结构 + main.py + config.py |
| 0.2 | 配置 SQLAlchemy 2.0 async + Alembic | 3h | database.py + alembic.ini + env.py |
| 0.3 | 编写全部 SQLAlchemy Models（16 张表） | 8h | models/*.py |
| 0.4 | 生成 Alembic 初始迁移并验证 | 2h | migrations/versions/001_initial.py |
| 0.5 | 编写 Pydantic Schemas（请求/响应） | 6h | schemas/*.py |
| 0.6 | 搭建 Docker Compose（PG + App） | 2h | docker-compose.yml |
| 0.7 | 配置 pytest + conftest（测试数据库） | 3h | tests/conftest.py |
| 0.8 | 实现全局错误处理中间件 | 2h | middleware/error_handler.py |
| 0.9 | 实现 JWT 认证中间件 | 3h | middleware/auth.py |
| 0.10 | 准备种子数据（JSON 格式） | 8h | seeds/*.json |
| 0.11 | 编写种子数据导入脚本 | 3h | seed.py |
| 0.12 | 配置 GitHub Actions CI | 3h | .github/workflows/ci.yml |
| 0.13 | 初始化微信小程序项目骨架 | 3h | miniprogram/ 基础结构 + app.json |
| 0.14 | 封装前端 HTTP 请求基础模块 | 2h | services/api.js |
| 0.15 | 配置腾讯云服务器 + 域名 + SSL | 4h | Nginx + HTTPS + 域名解析 |
| 0.16 | 部署 staging 环境并验证 | 3h | staging 可访问 |
| | **合计** | **~54h** | |

### 种子数据准备重点

| 数据 | Phase 0 最低要求 | 说明 |
|------|-----------------|------|
| subjects | 9 条（完整） | 系统预置，一次性写死 |
| knowledge_nodes | 数学 + 外语完整三级（~600 条），其他科目一级二级 | Phase 1 只展示 2 级，先保证 2 个科目深度完整 |
| milestones | 2025-2026 学年全部（~35 条） | 包含高三完整 + 高一高二通用节点 |
| action_cards | 6 组核心卡片（高考/等级考/春考/期末考 × 15d/3d） | Phase 2 才用，但 Phase 0 先准备好数据 |
| daily_quotes | 50 条（覆盖 8 个 category） | Phase 1 免费版需要 50 条基础库 |

### Phase 0 Acceptance Criteria

- [ ] `docker-compose up` 一键启动本地开发环境（PG + FastAPI）
- [ ] `make migrate && make seed` 成功导入全部 Schema 和种子数据
- [ ] 访问 `localhost:8000/docs` 能看到 Swagger UI（虽然还没有路由）
- [ ] `make test` 跑通（至少 conftest 能创建测试数据库）
- [ ] GitHub Actions CI 跑通（lint + test 两步）
- [ ] staging 环境可通过 HTTPS 访问 FastAPI 的 health check 端点
- [ ] 微信开发者工具可以加载小程序骨架页面
- [ ] PostgreSQL 中 16 张表全部创建成功，种子数据已导入

---

## 4. Phase 1 — 核心 MVP（Week 3-8）

### 目标
上线最小可用产品：Onboarding → 首页（倒计时 + 金句 + 里程碑） → 知识点浏览 → 基础成绩记录。全部免费，验证核心价值假设。

### Sprint 1：认证 + Onboarding + 学生档案（Week 3-4）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 1.1 | 后端：微信登录 API | 4h | `wechatpy` code2session → JWT 签发 |
| 1.2 | 后端：Student CRUD API | 4h | 含选科校验逻辑（高一可不选/高三必选） |
| 1.3 | 前端：欢迎页 | 2h | 品牌展示 + "开始使用"按钮 |
| 1.4 | 前端：年级选择页 | 3h | 三个大按钮 + 路由分支逻辑 |
| 1.5 | 前端：选科页 | 4h | 6 个科目按钮，恰好选 3 个，超选自动取消最早的 |
| 1.6 | 前端：1月外语考试确认页（高三） | 2h | 是/否/不确定 三选一 |
| 1.7 | 前端：区选择页 | 2h | 16 区列表 + "暂不选择" |
| 1.8 | 前端：完成页 | 3h | 时间线预览 + 金句 + "添加到桌面"引导 |
| 1.9 | 前端：services/auth.js + storage.js | 3h | token 管理 + 登录状态持久化 |
| 1.10 | 前端：services/student.js | 2h | 对接后端 Student API |
| 1.11 | 单元测试：选科校验逻辑 | 2h | 高一/高二/高三各种边界情况 |
| 1.12 | 集成测试：完整 Onboarding 流程 | 3h | 4 条路径全测 |
| | **合计** | **~34h** | |

**技术实现要点**：
- 微信登录用 `wx.login()` 获取临时 code → 后端用 code 调微信 `jscode2session` 接口换 openid → JWT 签发
- 本地开发时实现 mock 登录模式（跳过微信 API，用固定 openid），方便调试
- Onboarding 数据在全部页面填完后才调 `POST /api/students`（避免中途退出创建不完整数据）

### Sprint 2：首页 + 每日金句 + 里程碑浏览（Week 5-6）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 2.1 | 后端：金句分配 Service | 4h | 阶段感知 + 不重复 + 循环逻辑 |
| 2.2 | 后端：金句 API（today + favorite） | 3h | GET today / POST favorite / DELETE favorite |
| 2.3 | 后端：里程碑筛选 Service | 5h | 年级 × 选科 × 区 × 外语一考 四维 AND 筛选 |
| 2.4 | 后端：里程碑 API（list + next + CRUD custom） | 4h | 含倒计时天数计算 |
| 2.5 | 后端：Dashboard 聚合 API | 4h | 一次返回首页所有数据 |
| 2.6 | 后端：定时任务 — 每日金句分配 | 3h | APScheduler 08:00 触发 |
| 2.7 | 前端：首页布局与渲染 | 6h | 金句区 + 倒计时区 + 里程碑摘要 + 入口区 |
| 2.8 | 前端：quote-card 组件 | 3h | 显示金句 + 收藏按钮（Phase 1 免费版不含收藏） |
| 2.9 | 前端：countdown-card 组件 | 2h | 双倒计时（高一/二单个，高三双个） |
| 2.10 | 前端：里程碑时间线页 | 5h | 时间线 UI + 已过/未来分组 + 搜索 |
| 2.11 | 前端：添加自定义里程碑页 | 3h | 表单 + 日期选择器 |
| 2.12 | 单元测试：金句分配算法 | 4h | 阶段匹配/不重复/循环/年级过滤 |
| 2.13 | 单元测试：里程碑筛选逻辑 | 3h | 各种年级/选科/区组合 |
| | **合计** | **~49h** | |

**技术实现要点**：
- **金句分配算法**是核心复杂逻辑，必须充分测试：
  ```python
  # 伪代码
  def assign_daily_quote(student: Student) -> DailyQuote:
      phase = calculate_phase(student)  # 距最近考试天数 → phase
      candidates = query_quotes(
          grade=student.grade,
          phase=phase,
          exclude_shown=get_shown_quote_ids(student.id)
      )
      if not candidates:
          reset_quote_history(student.id)
          candidates = query_quotes(grade=student.grade, phase=phase)
      return candidates[0]  # ORDER BY display_order, RANDOM()
  ```
- **Dashboard 聚合接口**一次查询所有首页数据，减少前端请求数（目标 < 500ms）
- **里程碑筛选**用 PostgreSQL 的 JSONB 操作符：
  ```sql
  WHERE applicable_grades @> '["gao3"]'::jsonb
    AND (applicable_subjects IS NULL
         OR applicable_subjects ?| ARRAY['physics','chemistry','history'])
    AND (applicable_districts IS NULL
         OR applicable_districts @> '"huangpu"'::jsonb)
  ```

### Sprint 3：知识点浏览 + 成绩记录 + 打磨发布（Week 7-8）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 3.1 | 后端：知识点树 API（按科目+按年级过滤） | 3h | 嵌套查询，2 级默认 + 3 级按需加载 |
| 3.2 | 后端：成绩记录 CRUD API | 4h | 含满分自定义 + 得分率自动计算 |
| 3.3 | 后端：最近满分值 API | 1h | 各科上次满分，用于默认值填充 |
| 3.4 | 后端：付费权限中间件（Phase 1 仅校验免费版限制） | 3h | 免费版 <= 3 次考试 |
| 3.5 | 前端：知识点浏览页 | 5h | 可折叠树组件，默认展示 2 级 |
| 3.6 | 前端：knowledge-tree 组件 | 4h | 递归渲染 + 折叠/展开动画 |
| 3.7 | 前端：成绩列表页 | 3h | 按时间倒序，显示各科得分率 |
| 3.8 | 前端：成绩录入页 | 5h | 动态科目列表 + 满分可编辑 + 校验 |
| 3.9 | 前端：个人中心页 | 3h | 孩子档案管理 + 隐私政策 + 关于 |
| 3.10 | 前端：student-switcher 组件（多孩切换） | 3h | 顶部下拉切换 |
| 3.11 | 前端：upgrade-modal 组件（达限弹窗） | 2h | Phase 1 先做 UI 骨架 |
| 3.12 | 全局：UI 打磨（动效、loading、empty state） | 4h | 全页面检查 |
| 3.13 | 全局：错误处理 + 网络异常兜底 | 2h | 超时/无网络/服务端错误 |
| 3.14 | 集成测试：Onboarding → 首页 → 录入成绩 完整流程 | 3h | |
| 3.15 | 提交微信小程序审核 | 2h | 准备审核素材 + 类目选择 |
| | **合计** | **~47h** | |

**技术实现要点**：
- **知识点树**前端用递归组件渲染，2 级节点默认展开，3 级收起。展开 3 级时调异步 API 懒加载（减少首屏数据量）
- **成绩录入**的科目列表根据学生 `grade` 和 `selected_subjects` 动态生成。满分值从 `GET /exams/last-max-scores` 获取默认值
- **微信审核注意**：类目选"工具 → 信息查询"，不选"教育"类目（避免被要求提供教育资质）

### Phase 1 Acceptance Criteria

**功能验收**：
- [ ] 新用户可以完成 Onboarding（高一/高二未选科/高二已选科/高三 四条路径）
- [ ] 首页正确展示：今日金句 + 倒计时（高一单个/高三双个） + 近期里程碑
- [ ] 每日金句不重复，且根据年级/阶段智能匹配
- [ ] 里程碑时间线完整展示，支持添加/编辑/删除自定义里程碑
- [ ] 知识点树可浏览（默认 2 级），按年级展示对应科目
- [ ] 成绩可录入（含满分自定义），免费版限 3 次
- [ ] 多孩家庭可切换孩子，数据隔离正确
- [ ] 首页不展示焦虑式指标（"X天未使用"/"X个薄弱点"等）

**技术验收**：
- [ ] API 平均响应时间 < 500ms（Dashboard < 500ms，列表 < 300ms）
- [ ] 单元测试覆盖率 > 70%（核心 Service 层 > 90%）
- [ ] 金句分配算法测试覆盖：阶段匹配 / 不重复 / 全部展示后循环 / 年级过滤
- [ ] 里程碑筛选算法测试覆盖：年级 / 选科 / 区 / 外语一考 各种组合
- [ ] CI pipeline 全绿
- [ ] staging 环境稳定运行 3 天以上

**业务验收（上线后 2 周内观察）**：
- [ ] Onboarding 完成率 > 80%
- [ ] 7 天留存率 > 35%
- [ ] 金句查看率 > 50%（每天至少看一次首页）
- [ ] 里程碑页面访问率 > 40%
- [ ] **Go/No-Go 判定**：任一业务指标未达标 → 暂停后续开发，重新评估核心假设

---

## 5. Phase 1.5 — 错题本 + 成长记录（Week 9-12）

### 目标
新增错题拍照归档和成长记录功能，免费版有容量限制，验证这两个功能的使用率和付费转化潜力。

### Sprint 4：错题拍照记录本（Week 9-10）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 4.1 | 后端：COS 图片上传 Service | 4h | 临时上传凭证生成 + 签名 URL |
| 4.2 | 后端：图片上传 API | 2h | POST /api/upload/image → 返回 COS 临时凭证 |
| 4.3 | 后端：错题 CRUD API | 5h | 含分页 + 多维筛选 + 统计 |
| 4.4 | 后端：错题统计 API | 2h | 按科目/错误类型/知识点分组统计 |
| 4.5 | 后端：免费版容量限制（10 道） | 2h | permission 中间件扩展 |
| 4.6 | 前端：图片压缩工具 | 3h | wx.compressImage → 1200px / 80% / JPEG |
| 4.7 | 前端：错题录入页（3 步流程） | 6h | 拍照 → 选科目/知识点 → 标注 → 保存 |
| 4.8 | 前端：错题列表页 | 5h | 筛选器 + 卡片列表 + 统计摘要 |
| 4.9 | 前端：错题详情页（大图） | 3h | 图片全屏查看 + image-viewer 组件 |
| 4.10 | 前端：subject-picker 组件增强 | 2h | 支持按年级动态过滤科目 |
| 4.11 | 后端：定时任务 — 孤立图片清理 | 2h | 每周日 03:00，清理上传但未关联的图片 |
| 4.12 | 集成测试：错题完整流程 | 3h | 录入→列表→筛选→详情→删除→容量限制 |
| | **合计** | **~39h** | |

**技术实现要点**：
- **图片上传流程**：前端获取临时凭证 → 前端直传 COS（不经过后端，省带宽） → 后端只存 image_key
- **图片安全**：所有图片 URL 使用 COS 临时签名链接（2 小时有效），不公开访问
- **错题筛选**用 PostgreSQL 组合索引：`(student_id, subject_id)` + `(student_id, created_at DESC)`
- **免费版限制**在后端 API 层校验，前端也做预检查（减少无效请求）

### Sprint 5：成长记录 + 成绩进步检测（Week 11-12）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 5.1 | 后端：成长记录 CRUD API | 4h | 含自动匹配金句 |
| 5.2 | 后端：成长记录按学年分组 API | 2h | 按学年倒序 + 时间线数据结构 |
| 5.3 | 后端：成绩进步自动检测 Service | 4h | 同类考试同科目得分率对比，阈值 >= 10% |
| 5.4 | 后端：成绩录入 API 增强（返回 progress_detected） | 2h | 录入后自动检测并返回进步信息 |
| 5.5 | 后端：免费版容量限制（成长记录 5 条） | 1h | |
| 5.6 | 前端：成长记录时间线页 | 5h | 按学年分组 + 时间线 UI + 类型图标 |
| 5.7 | 前端：添加成长记录页 | 5h | 5 种类型切换 + 奖项详情表单 + 拍照上传 |
| 5.8 | 前端：成绩进步弹窗 | 3h | 录入成绩后检测到进步 → 弹窗 → 跳转添加成长记录（预填） |
| 5.9 | 前端：首页摘要区更新 | 2h | 展示错题总数 + 成长记录数 |
| 5.10 | 前端：TabBar 调整 | 1h | 4 Tab：首页 / 错题本 / 成长册 / 我的 |
| 5.11 | 单元测试：成绩进步检测 | 3h | 各种边界（首次录入/跨类型/刚好 10%/不足 10%） |
| 5.12 | 集成测试：成绩录入→进步检测→成长记录 完整流程 | 3h | |
| | **合计** | **~35h** | |

**技术实现要点**：
- **成绩进步检测**是触发型（不是定时任务），在 `POST /exams` 的 Service 层执行：
  ```python
  # 伪代码
  def detect_progress(student_id, new_exam) -> list[ProgressDetected]:
      results = []
      for score in new_exam.scores:
          prev = get_previous_same_type_exam_score(student_id, new_exam.exam_type, score.subject_id)
          if prev and (score.score_rate - prev.score_rate) >= 10.0:
              results.append(ProgressDetected(subject=score.subject_id, improvement=...))
      return results
  ```
- **成长记录保存时自动匹配金句**：根据 record_type 映射到 quote_category，随机选一条

### Phase 1.5 Acceptance Criteria

**功能验收**：
- [ ] 错题拍照录入完整流程（拍照 → 选科目 → 选知识点 → 标注 → 保存）平均耗时 < 45 秒
- [ ] 错题列表支持按科目/知识点/错误类型/来源/时间 筛选
- [ ] 错题统计正确展示各科错题数量
- [ ] 免费版达到 10 道错题上限时，正确弹出升级引导
- [ ] 成长记录支持 5 种类型录入（奖项/进步/表现/突破/备忘）
- [ ] 成长记录时间线按学年正确分组展示
- [ ] 成绩录入后自动检测进步（同类考试同科目得分率提升 >= 10%）
- [ ] 进步检测触发后弹窗提示，可一键跳转记录成长册

**技术验收**：
- [ ] 图片上传成功率 > 99%（本地测试 100 张图片）
- [ ] 图片压缩后大小 < 2MB（原图 10MB 以内）
- [ ] 错题列表查询性能 < 300ms（模拟 100 道错题）
- [ ] 成绩进步检测算法单元测试 100% 覆盖

**业务验收（上线后 4 周内观察）**：
- [ ] 错题本使用率 > 40%（至少录入 1 道错题的用户占比）
- [ ] 成长记录使用率 > 30%（至少记录 1 条的用户占比）
- [ ] 错题触达上限率 > 20%（达到 10 道免费上限的用户占比）
- [ ] **付费信号判定**：如果错题触达上限率 < 10% → 考虑调整容量限制策略或降低错题本优先级

---

## 6. Phase 2 — 付费变现 + 完整功能（Week 13-20）

### 目标
推出付费订阅（标准版），完善行动卡片、完整金句库、分享、趋势图等进阶功能。实现可持续的商业模式。

### Sprint 6：微信支付 + 订阅系统（Week 13-14）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 6.1 | 后端：微信支付集成 | 8h | 统一下单 + 回调处理 + 退款接口 |
| 6.2 | 后端：订阅管理 API | 5h | 当前状态 / 升级 / 续费 |
| 6.3 | 后端：7 天免费试用逻辑 | 3h | 注册时自动创建试用订阅 |
| 6.4 | 后端：付费权限中间件完善 | 4h | 按 plan 控制全部功能访问 |
| 6.5 | 前端：订阅管理页 | 4h | 套餐对比 + 购买按钮 + 支付流程 |
| 6.6 | 前端：upgrade-modal 完善 | 3h | 各触发节点的差异化文案 |
| 6.7 | 前端：permission.js 工具完善 | 2h | 前端预检查（减少 403 请求） |
| 6.8 | 集成测试：支付流程（用微信沙箱） | 4h | 下单→支付→回调→状态更新 |
| | **合计** | **~33h** | |

**技术实现要点**：
- **微信支付**使用 `wechatpy` 库的 V3 API，JSAPI 支付方式
- **支付回调幂等性**：用 Redis SETNX 确保回调只处理一次
- **试用到期处理**：定时任务每日检查，到期后降为免费版
- **付费转化触发节点**（前端实现）：
  - 错题达 10 道 → "错题本已满，升级解锁无限存储"
  - 成长记录达 5 条 → "成长册已满，升级继续记录闪光时刻"
  - 成绩录入第 4 次 → "升级查看趋势分析"
  - 点击 3 级知识点展开 → "升级解锁更细知识点"
  - 试用第 5 天 → "已记录 X 道错题，升级继续使用"

### Sprint 7：里程碑行动卡片 + 推送通知（Week 15-16）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 7.1 | 后端：行动卡片 API（含勾选持久化） | 4h | 获取卡片 + 更新勾选状态 |
| 7.2 | 后端：定时任务 — 里程碑提醒（含微信订阅消息） | 6h | 每日检查 + 发送订阅消息 |
| 7.3 | 后端：提醒记录 API | 2h | 标记已打开 + 查询历史 |
| 7.4 | 后端：行动卡片与错题本联动 | 3h | 卡片中展示"XX科有N道错题" |
| 7.5 | 前端：行动卡片详情页 | 6h | 可勾选行动项 + 跳转联动 + 完成态 |
| 7.6 | 前端：action-item 组件 | 3h | 勾选动画 + 详情展开 + 跳转 |
| 7.7 | 前端：订阅消息引导（Onboarding + 首次行动卡片） | 3h | wx.requestSubscribeMessage |
| 7.8 | 前端：首页行动提醒区域 | 2h | 有活跃行动卡片时展示入口 |
| 7.9 | 集成测试：提醒→卡片→勾选 完整流程 | 3h | |
| | **合计** | **~32h** | |

**技术实现要点**：
- **微信订阅消息**需在微信公众平台申请模板，使用一次性订阅（每次获取一次授权）
- **行动卡片与错题本联动**：渲染行动卡片时，如果有"翻错题本"行动项，查询该学生的错题统计，动态插入"数学12道 物理8道"

### Sprint 8：完整金句库 + 分享 + 3 级知识点（Week 17-18）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 8.1 | 内容：扩充金句库到 300+ 条 | 6h | 按 8 个 category 均匀分布 |
| 8.2 | 后端：金句分享图片生成 API | 5h | Canvas / Pillow 生成带倒计时+金句+小程序码的图片 |
| 8.3 | 后端：金句收藏 API 完善 | 1h | 已有骨架，补充标准版权限检查 |
| 8.4 | 前端：金句收藏功能 | 2h | 首页收藏按钮 + 收藏列表页 |
| 8.5 | 前端：金句分享功能 | 4h | 生成图片 → 保存到相册 / 分享到微信 |
| 8.6 | 后端：知识点树 3 级展开 API | 2h | 按需加载子节点 + 标准版权限 |
| 8.7 | 内容：补全所有 9 科知识点到三级 | 8h | 参考教材目录和考纲 |
| 8.8 | 前端：knowledge-tree 3 级展开 | 2h | 展开时调 API 懒加载 + 权限提示 |
| 8.9 | 前端：桌面快捷方式引导 | 2h | wx.addToHomeScreen() + 手动引导 |
| | **合计** | **~32h** | |

**技术实现要点**：
- **金句图片生成**用 Python `Pillow` 库：
  - 背景：渐变色/精选图片
  - 内容：金句文字 + 倒计时天数 + 小程序码
  - 缓存：同一天同一条金句只生成一次，存 COS，7 天后清理
- **300+ 金句**可以借助 AI 辅助生成初稿，人工审核修改

### Sprint 9：成绩趋势 + 成长档案导出 + 学校进度（Week 19-20）

| # | 任务 | 估时 | 技术要点 |
|---|------|------|---------|
| 9.1 | 后端：成绩趋势 API | 3h | 按科目返回得分率序列 + 整体趋势判定 |
| 9.2 | 前端：成绩趋势图页 | 5h | 折线图（wx-charts 或 echarts-for-weixin） |
| 9.3 | 后端：成长档案导出 API（PDF/长图） | 6h | Pillow / reportlab 生成 PDF |
| 9.4 | 前端：成长档案导出页 | 3h | 预览 + 导出格式选择 + 下载保存 |
| 9.5 | 后端：学校复习进度 CRUD API | 3h | 含错题本联动提示 |
| 9.6 | 前端：学校复习进度记录页 | 3h | 简单表单 + 联动提示展示 |
| 9.7 | 后端：Redis 缓存集成 | 4h | Dashboard 缓存 + Rate Limiting |
| 9.8 | 全局：性能优化 | 3h | 慢查询优化 + 缓存命中率 |
| 9.9 | 全局：UI 打磨第二轮 | 3h | 全流程体验走查 |
| 9.10 | 集成测试：付费功能全流程 | 4h | 免费→试用→购买→功能解锁 |
| | **合计** | **~37h** | |

**技术实现要点**：
- **成绩趋势图**用 `echarts-for-weixin` 或 `wx-charts`，纵轴为得分率（百分比），横轴为考试名称
- **PDF 导出**用 `reportlab` 生成：
  - 封面：孩子名字 + "高中三年成长档案"
  - 内容：按学年分组的时间线 + 证书照片缩略图 + 成绩趋势图
  - 结尾：总结统计（N 个闪光时刻）

### Phase 2 Acceptance Criteria

**功能验收**：
- [ ] 微信支付完整流程（选方案 → 支付 → 回调 → 状态更新）正常工作
- [ ] 标准版月付/年付/全程包 三种方案均可购买
- [ ] 7 天免费试用自动开启和到期降级
- [ ] 所有付费转化触发节点正确弹出升级引导
- [ ] 里程碑前 15 天 / 前 3 天自动发送微信订阅消息
- [ ] 行动卡片可查看、可勾选、勾选状态持久化
- [ ] 行动卡片与错题本/知识点树正确联动跳转
- [ ] 完整金句库 300+ 条不重复展示
- [ ] 金句可收藏、可生成分享图片、可保存到相册
- [ ] 知识点树 3 级展开正常（标准版以上）
- [ ] 成绩趋势折线图正确渲染
- [ ] 成长档案可导出 PDF 和长图
- [ ] 学校复习进度可记录，且与错题本联动提示正确

**技术验收**：
- [ ] 微信支付回调幂等性验证通过
- [ ] Redis 缓存命中率 > 80%（Dashboard 接口）
- [ ] 全部 API 响应时间达标（见 Spec 性能要求）
- [ ] 单元 + 集成测试覆盖率 > 75%

**业务验收（上线后 4-8 周内观察）**：
- [ ] 30 天留存率 > 40%
- [ ] 免费 → 标准版转化率 > 5%
- [ ] 高中全程包占付费用户比例 > 35%
- [ ] 金句分享率 > 15%（至少分享过一次的用户）
- [ ] NPS > 40
- [ ] **盈利信号判定**：如果付费转化率 < 2% → 重新评估定价策略或免费版功能边界

---

## 7. Phase 3 — AI 增值功能（Week 21-28）

> **前置条件**：Phase 2 业务指标达标，付费转化率 > 5%，确认 AI 功能合规性（错题分类需法律确认）

### 目标
推出高级版，通过 AI 功能提高 ARPU 和用户粘性。

### Sprint 10-11：AI 家长顾问 + 个性化行动建议（Week 21-24）

| 任务 | 估时 | 技术要点 |
|------|------|---------|
| AI 家长顾问对话 API | 8h | 调用 LLM API（通义千问/文心一言），System Prompt 限定合规边界 |
| 对话上下文管理 | 4h | Redis 存储会话历史，限制 10 轮/天 |
| 合规过滤层 | 6h | 检测用户输入和 AI 输出是否涉及学科辅导，自动拦截 |
| 个性化行动建议生成 | 6h | 根据选科+时间节点+错题分布，LLM 生成定制化建议 |
| 前端：AI 对话页面 | 6h | 聊天 UI + 流式响应 |
| 前端：个性化行动卡片 | 4h | AI 生成内容的特殊展示样式 |
| AI Token 成本控制 | 4h | 缓存相似问题、分级响应、速率限制 |

### Sprint 12-13：AI 金句 + 错题分类 + 月度报告（Week 25-28）

| 任务 | 估时 | 技术要点 |
|------|------|---------|
| AI 个性化金句生成 | 4h | 结合孩子名字/选科/阶段生成金句 |
| AI 错题分类助手（需合规确认） | 6h | OCR 识别题目 → 分类到知识点（不给答案） |
| AI 月度成长报告 | 6h | 总结本月成绩变化 + 错题趋势 + 成长亮点 |
| 前端：月度报告页 | 4h | 图表 + AI 文字总结 |
| 高级版权限控制 | 3h | premium 功能访问限制 |

### Phase 3 Acceptance Criteria

**功能验收**：
- [ ] AI 家长顾问可正常对话，每日上限 10 轮
- [ ] AI 输出 100% 不涉及学科知识讲解和题目解答（合规测试 200+ 条 query）
- [ ] 个性化行动建议基于学生实际数据生成
- [ ] AI 金句融入孩子名字/选科信息
- [ ] 月度成长报告正确汇总本月数据

**技术验收**：
- [ ] AI 响应时间 < 5s（流式首 token < 1s）
- [ ] AI Token 成本 < ¥0.5/用户/天（高级版用户）
- [ ] 合规过滤层准确率 > 99%

**业务验收**：
- [ ] 标准版 → 高级版升级率 > 15%
- [ ] 高级版用户 ARPU > ¥35/月
- [ ] AI 顾问使用频率 > 3 次/周

---

## 8. Phase 4 — 跨地区扩展（Week 29+）

> **前置条件**：Phase 3 业务指标达标，上海市场验证成功

### 目标
将产品扩展到浙江、北京等新高考省份。

### 核心工作

| 任务 | 说明 |
|------|------|
| 底层架构可配置化 | 科目体系/分值/知识点树/里程碑 按省份配置 |
| 浙江省适配 | 知识点树 + 里程碑 + 科目体系（浙江 7 选 3） |
| 北京市适配 | 知识点树 + 里程碑 + 科目体系 |
| 原生 App（可选） | iOS Widget / Android 小组件 |

### Phase 4 Acceptance Criteria

- [ ] 新省份上线只需配置数据（JSON），不需要改代码
- [ ] 浙江省用户可以完成 Onboarding 并正常使用全部功能
- [ ] 知识点树准确覆盖浙江高考考纲 > 95%

---

## 9. 风险应对

| 风险 | 等级 | 应对策略 | 触发信号 |
|------|------|---------|---------|
| **微信支付 Python 集成问题** | 🟡 中 | Phase 0 最后一天做 Spike 验证 `wechatpy` 支付功能；如不可行，Phase 2 写一个轻量 Node.js 支付微服务 | Phase 0 Spike 失败 |
| **微信小程序审核被拒** | 🟡 中 | 类目选"工具-信息查询"而非"教育"；准备好合规说明文档；首次审核提前 5 天提交 | 审核反馈要求教育资质 |
| **核心假设不成立（留存不达标）** | 🔴 高 | Phase 1 设定 Go/No-Go 指标，不达标则暂停开发，用 2 周做用户访谈重新定位 | 7 天留存 < 35% |
| **错题本使用率低** | 🟡 中 | 如果 < 20%，考虑简化流程（一键拍照，不选知识点）或降低功能优先级 | Phase 1.5 数据 |
| **付费转化率过低** | 🟡 中 | 调整免费版限制（更严格或更宽松）、调整定价、增加试用期 | Phase 2 转化率 < 2% |
| **图片存储成本超预算** | 🟢 低 | 免费版严格限制容量；图片压缩更激进（800px / 70%）；冷数据转低频存储 | 月存储费 > ¥100 |
| **AI 合规问题** | 🔴 高 | Phase 3 AI 功能全部需合规确认后才上线；AI 输出增加人工审核抽检机制 | 法律顾问标记风险 |
| **单人开发瓶颈** | 🟡 中 | 严格按 Sprint 执行，不做 scope creep；Phase 2 完成后评估是否需要外包前端 | 连续 2 个 Sprint 延期 |

---

## 10. 附录 — 关键技术实现参考

### A. FastAPI 项目初始化依赖

```
# server/requirements.txt (Phase 1 核心依赖)

fastapi==0.115.*
uvicorn[standard]==0.30.*
sqlalchemy[asyncio]==2.0.*
asyncpg==0.30.*             # PostgreSQL async driver
alembic==1.14.*
pydantic==2.10.*
pydantic-settings==2.7.*
python-jose[cryptography]==3.3.*   # JWT
wechatpy==1.8.*             # 微信 SDK
cos-python-sdk-v5==1.9.*    # 腾讯云 COS
httpx==0.28.*               # HTTP client (调微信API)
apscheduler==3.10.*         # 定时任务
python-multipart==0.0.*     # 文件上传
Pillow==11.*                # 图片处理/分享图生成
pytest==8.*                 # 测试
pytest-asyncio==0.24.*
ruff==0.8.*                 # Lint + Format
mypy==1.13.*                # 类型检查
```

### B. Docker Compose 本地开发

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: gaokao_companion
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  # Phase 2+ 才需要
  # redis:
  #   image: redis:7-alpine
  #   ports:
  #     - "6379:6379"

volumes:
  pgdata:
```

### C. Makefile

```makefile
.PHONY: dev test migrate seed lint

dev:
	cd server && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd server && pytest tests/ -v --tb=short

test-unit:
	cd server && pytest tests/unit/ -v

test-cov:
	cd server && pytest tests/ --cov=app --cov-report=html

migrate:
	cd server && alembic upgrade head

migrate-new:
	cd server && alembic revision --autogenerate -m "$(msg)"

seed:
	cd server && python seed.py

lint:
	cd server && ruff check app/ && ruff format --check app/

format:
	cd server && ruff format app/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
```

### D. 工期总览表

| Phase | Sprint | 周次 | 预估工时 | 核心交付物 |
|-------|--------|------|---------|-----------|
| **Phase 0** | Sprint 0 | W1-2 | ~54h | 基础设施 + DB Schema + 种子数据 |
| **Phase 1** | Sprint 1 | W3-4 | ~34h | 认证 + Onboarding + 学生档案 |
|             | Sprint 2 | W5-6 | ~49h | 首页 + 金句 + 里程碑 |
|             | Sprint 3 | W7-8 | ~47h | 知识点 + 成绩 + 打磨发布 |
| **Phase 1.5** | Sprint 4 | W9-10 | ~39h | 错题拍照记录本 |
|               | Sprint 5 | W11-12 | ~35h | 成长记录 + 进步检测 |
| **Phase 2** | Sprint 6 | W13-14 | ~33h | 微信支付 + 订阅系统 |
|             | Sprint 7 | W15-16 | ~32h | 行动卡片 + 推送 |
|             | Sprint 8 | W17-18 | ~32h | 完整金句 + 分享 + 3级知识点 |
|             | Sprint 9 | W19-20 | ~37h | 趋势图 + 导出 + 学校进度 |
| **合计 Phase 0-2** | | **20 周** | **~392h** | |
| **Phase 3** | Sprint 10-13 | W21-28 | ~60h | AI 增值功能 |
| **Phase 4** | TBD | W29+ | TBD | 跨地区扩展 |

> **说明**：以上估时基于单人全栈开发，每周投入约 20-25 小时。如每周投入 40 小时（全职），总工期可压缩到 10-12 周完成 Phase 0-2。

---

*End of Development Plan*
