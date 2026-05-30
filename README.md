# 高考家长帮 (Gaokao Parent Companion)

一款面向高中生家长的微信小程序，通过里程碑驱动的行动提醒、每日励志金句、错题拍照归档和孩子成长记录，帮助家长在高考备考全程中不焦虑、不缺席、不越界。

支持**本地账号系统**：一个账号对应一个孩子，数据完全隔离。家长可以为每个孩子创建独立账号，一键切换，无需多微信或多手机号。

架构已预留**多省份扩展**：当前首发上海地区，数据模型已支持按省份/地区隔离里程碑、科目满分等配置。

A WeChat mini-program for parents of high school students, providing milestone-driven action reminders, daily inspirational quotes, error note photo archival, and growth records. Supports a **local account system**: one account per child with fully isolated data. Architecture is **multi-province ready** — currently launching with Shanghai, with province-aware data isolation built-in.

---

## 📋 Project Overview

### 一句话描述
纯家长端工具，孩子无需任何操作。家长通过里程碑时间提醒、通用行动建议、金句、错题拍照归档（不解题）、成长记录来陪伴孩子备考。

A parent-only tool requiring no action from the child. Parents use milestone reminders, action suggestions, quotes, error note archival (without solutions), and growth records to accompany their child's exam preparation.

### 目标用户
- 高中考生家长（40-50岁），首发聚焦上海地区
- 熟练使用微信但不擅长复杂App

Shanghai high school student parents (ages 40-50), familiar with WeChat but not complex apps.

### 合规红线 (Compliance Constraints)
- ❌ 不得提供学科知识点讲解、题目解答、解题过程
- ❌ 不得提供拍照搜题、题库练习、作业批改功能
- ❌ 不得推荐付费教师、课程或培训机构
- ❌ 不得生成"每日复习计划""个性化复习任务"等学科辅导内容
- ✅ AI 聊天仅限家长陪伴建议、学习节奏指导、心理鼓励、时间管理建议
- ✅ 提供里程碑时间提醒、通用行动建议、金句、错题拍照归档（不解题）、成长记录

---

## 🏗️ Architecture

### Tech Stack

| Component | Technology | Rationale |
|-----------|-------------|-----------|
| **Frontend** | WeChat Mini Program (WXML + WXSS + JS) | Native WeChat ecosystem, no app installation |
| **Backend** | Python FastAPI | Auto Swagger docs, Pydantic validation, AI-ready |
| **Database** | PostgreSQL 16 | JSONB for milestone filtering, native ARRAY types |
| **ORM** | SQLAlchemy 2.0 (async) | Modern async support, type-safe |
| **Migration** | Alembic | Database version control |
| **Scheduler** | APScheduler (AsyncIOScheduler) | Daily quote assignment + milestone reminders |
| **AI/LLM** | DashScope / OpenAI-compatible API | AI chat, monthly reports, suggestions, classification |
| **Cache** | Redis (optional, graceful fallback) | Rate limiting, response caching |
| **Storage** | Tencent Cloud COS | Image storage for error notes |
| **Auth** | WeChat Login (wx.login) + JWT / Local Account System | Flexible auth options |
| **Payment** | WeChat Pay V3 (JSAPI) | Subscription monetization |
| **Deployment** | Docker Compose (local) / Tencent Cloud (prod) | Containerized, cloud-native |

### System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      WeChat Mini Program                          │
│  Pages: onboarding / index / milestones / exams / errors /       │
│         growth / quotes / knowledge / ai-chat / profile          │
│  29 JSON files · 34 JS files · 26+ pages · services · utils      │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS (RESTful JSON)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  15 API Routers                                          │    │
│  │  auth · students · milestones · action-cards · dashboard │    │
│  │  quotes · knowledge · exams · error-notes · growth       │    │
│  │  subscription · upload · school-progress · ai-chat · ai  │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                      │
│  ┌──────────────────────────┴──────────────────────────────┐    │
│  │  25+ Services (Business Logic Layer)                     │    │
│  │  auth · student · milestone · quote · exam · error-note │    │
│  │  growth · dashboard · knowledge · action-card · payment  │    │
│  │  subscription · image · cache · ai-chat · ai-quote       │    │
│  │  ai-monthly-report · ai-action-suggestion · ai-classify  │    │
│  │  compliance-filter · llm-client · ai-cost-control · ...  │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                      │
│  ┌──────────────────────────┴──────────────────────────────┐    │
│  │  Middleware Layer                                        │    │
│  │  JWT Auth · Permission Checker · Error Handler           │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                      │
│  ┌──────────────────────────┴──────────────────────────────┐    │
│  │  APScheduler                                            │    │
│  │  Daily quote assignment (08:00) · Reminder check (09:00)│    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │PostgreSQL │ │ Tencent  │ │  Redis   │
            │ 16 tables │ │   COS    │ │(optional)│
            │           │ │ (Images) │ │ (Cache)  │
            └──────────┘ └──────────┘ └──────────┘
```

---

## 📁 Directory Structure

```
Gaokao-review-new/
├── Analysis-folder/              # Product vision iterations
├── Implementation/
│   ├── Spec.md                   # Full technical specification (16 tables, 25 pages)
│   └── Development-Plan.md       # Sprint breakdown, timeline
├── miniprogram/                  # WeChat mini-program frontend
│   ├── app.js/json/wxss         # App entry & global styles
│   ├── pages/                    # 34+ pages (136+ files)
│   │   ├── onboarding/          # Welcome, grade select, subject select (6 pages)
│   │   ├── index/               # Home page (dashboard)
│   │   ├── milestones/          # Timeline, action card, add custom (3 pages)
│   │   ├── exams/               # List, add, trend (3 pages)
│   │   ├── errors/              # List, add, detail (3 pages)
│   │   ├── growth/              # Timeline, add, export (3 pages)
│   │   ├── quotes/              # Favorites (1 page)
│   │   ├── knowledge/           # Browse (1 page)
│   │   ├── school-progress/     # List (1 page)
│   │   ├── ai/                  # Chat, chat-history, monthly-report, suggestions (4 pages)
│   │   └── profile/             # Settings, student-manage, subscription, privacy, about, account-switch (6 pages)
│   ├── services/                # 9 service modules (api, auth, account, student, sync, upload, ...)
│   ├── utils/                   # Date, storage helpers
│   └── constants/               # Subjects, regions, plans
├── server/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py              # FastAPI app entry (15 routers, lifespan, CORS, error handlers)
│   │   ├── config.py            # Settings (pydantic-settings, 40+ env vars)
│   │   ├── database.py          # Async engine & session
│   │   ├── models/              # 14 SQLAlchemy 2.0 models
│   │   ├── schemas/             # 11 Pydantic v2 schema files
│   │   ├── middleware/          # JWT auth, error handler, permission checker
│   │   ├── routers/             # 15 API route modules
│   │   ├── services/            # 25+ business logic service modules
│   │   ├── jobs/                # APScheduler (daily quotes, reminders)
│   │   └── utils/               # Date helpers, WeChat SDK
│   ├── migrations/              # Alembic migrations
│   │   ├── env.py               # Migration config (imports all models)
│   │   └── versions/            # 2 migration files (initial schema + AI chat tables)
│   ├── seeds/                   # Reference data JSON
│   │   ├── subjects.json
│   │   ├── provinces.json       # Province configs (Shanghai initially)
│   │   ├── regions.json         # Region/district data keyed by province
│   │   ├── knowledge_tree/      # 9 subject JSON files (365 nodes)
│   │   ├── milestones.json      # 50 system milestones
│   │   ├── action_cards.json    # Action card templates
│   │   └── quotes.json          # 60 daily quotes
│   ├── seed.py                  # Seed import script
│   ├── tests/                   # 12+ unit & integration tests
│   ├── requirements.txt         # Python dependencies
│   ├── pyproject.toml           # pytest config
│   └── alembic.ini              # Alembic config
├── docker-compose.yml           # PostgreSQL 16 dev + test
├── Makefile                     # Common commands
├── .env.example                 # Environment template
├── .github/workflows/ci.yml     # GitHub Actions CI (lint + typecheck + test)
└── README.md                    # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- WeChat Developer Tools (for mini-program development)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/JaniceWei99/Gaokao-Review-New.git
cd Gaokao-Review-New
```

2. **Start PostgreSQL**
```bash
docker compose up -d
```

3. **Set up Python environment**
```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings (defaults work for local dev)
```

5. **Run database migration**
```bash
alembic upgrade head
```

6. **Seed reference data**
```bash
python seed.py
```

7. **Start FastAPI server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Access API docs**
```
http://localhost:8000/docs
http://localhost:8000/redoc
```

### Using Makefile

```bash
# Full setup (docker up + migrate + seed)
make setup

# Start development server
make dev

# Run tests
make test
make test-unit
make test-cov

# Code quality
make lint
make format
make typecheck

# Database
make migrate
make migrate-new msg="description"
make seed
make fresh  # docker reset + migrate + seed
```

---

## 🧪 Testing

```bash
cd server

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
```

Current test coverage: 12+ tests including health check, auth token creation/decoding, milestone service, quote service, and student operations.

CI pipeline (GitHub Actions) runs on every push to `main`:
1. `ruff` linting
2. `ruff format` check
3. `mypy` type checking
4. Alembic migrations (test database)
5. `pytest` with coverage

---

## 📊 Database Schema

### 14 Tables

| Table | Rows (seeded) | Description |
|-------|---------------|-------------|
| subjects | 9 | 3 required + 6 elective subjects |
| knowledge_nodes | 365 | 3-level knowledge tree (9 subjects) |
| milestones | 35 | System milestones (2025-2026 school year) |
| action_cards | 8 | Action card templates (15d/3d before events) |
| daily_quotes | 60 | Inspirational quotes (8 categories) |
| users | 0 | Parent accounts (created on WeChat login) |
| students | 0 | Child profiles (created during onboarding, province-aware) |
| exams | 0 | Exam records with custom max scores |
| exam_scores | 0 | Exam scores per subject |
| error_notes | 0 | Error note photos with metadata |
| growth_records | 0 | Growth timeline records (5 types) |
| user_quote_favorites | 0 | Favorited quotes |
| user_quote_history | 0 | Quote display history (pre-assigned daily) |
| milestone_reminders | 0 | User-specific reminder settings |
| school_progress | 0 | School review progress tracking |
| user_subscriptions | 0 | Subscription plans (free/standard/premium) |
| ai_chat_sessions | 0 | AI chat conversation sessions |
| ai_chat_messages | 0 | Individual AI chat messages |

See `Implementation/Spec.md` for detailed table definitions.

---

## 📈 Development Progress

### Phase 0: Infrastructure Scaffolding ✅ (Complete)

**Status**: Phase 0 foundation complete

- ✅ FastAPI server with health endpoint, CORS, global error handlers
- ✅ 14 SQLAlchemy 2.0 models with full relationships & indexes
- ✅ Alembic migration (2 migration files covering all tables)
- ✅ 11 Pydantic v2 request/response schema modules
- ✅ JWT auth middleware + permission checker + error handler
- ✅ Seed data: 9 subjects, 365 knowledge nodes, 35 milestones, 8 action cards, 60 daily quotes
- ✅ WeChat mini-program skeleton: 34+ pages, 9 services, utils, constants
- ✅ Docker Compose (PostgreSQL 16 dev + test)
- ✅ GitHub Actions CI, Makefile, pytest (12+ tests passing)
- ✅ Local account system (password-protected, one-click switch)
- ✅ Redis cache service (optional, graceful fallback)

---

### Phase 1: Core MVP ✅ (Complete)

| Feature | Status | Details |
|---------|--------|---------|
| WeChat Login (wx.login) + JWT | ✅ Complete | `auth.py` router + middleware |
| Student Profile CRUD | ✅ Complete | Onboarding flow with grade/subject/district selection |
| Milestone Timeline | ✅ Complete | System milestones + custom CRUD + filtering |
| Daily Quotes | ✅ Complete | 60 quotes in 8 categories, pre-assigned daily |
| Dashboard | ✅ Complete | Countdown, quote, milestone summary, score summary |
| Knowledge Tree | ✅ Complete | 2-level browse (365 nodes across 9 subjects) |
| Exam Records | ✅ Complete | CRUD + custom max scores + score rate calculation |
| Multi-Child Support | ✅ Complete | Account switching + data isolation |
| Onboarding Flow | ✅ Complete | Welcome → Grade → Subjects → English Exam → District → Complete |
| Profile/Settings | ✅ Complete | Student management, privacy, about pages |

**API Routers Implemented**:
- `auth.py` — WeChat login, token refresh, local account CRUD
- `students.py` — Student CRUD, onboarding, switching
- `milestones.py` — System + custom milestones, reminders
- `quotes.py` — Daily quote, favorites, history
- `dashboard.py` — Aggregated dashboard data
- `knowledge.py` — Knowledge tree browsing
- `exams.py` — Exam CRUD, score trends

---

### Phase 1.5: Error Notes + Growth Records ✅ (Complete)

| Feature | Status | Details |
|---------|--------|---------|
| Error Note Photo Upload | ✅ Complete | COS storage with compression |
| Error Note CRUD | ✅ Complete | List/detail/filter/delete with pagination |
| Error Note Statistics | ✅ Complete | By subject, error type, knowledge point |
| Free Tier Limit (10 notes) | ✅ Complete | Permission middleware enforcement |
| Growth Records Timeline | ✅ Complete | 5 types (award/progress/performance/breakthrough/memo) |
| Growth Record Add | ✅ Complete | Form + photo upload |
| Growth Record Export | ✅ Complete | PDF/long image generation (Pillow) |
| Score Progress Detection | ✅ Complete | Auto-detect ≥10% improvement → prompt growth record |

**Additional API Routers**:
- `error_notes.py` — Error note CRUD + statistics
- `growth_records.py` — Growth record CRUD + export
- `upload.py` — Image upload with COS temporary credentials

---

### Phase 2: Monetization + Complete Features 🔄 (Mostly Complete)

| Feature | Status | Details |
|---------|--------|---------|
| WeChat Pay V3 (JSAPI) | ✅ Complete | Mock mode for development, production-ready |
| Subscription Tiers | ✅ Complete | Free / Standard / Premium (monthly/yearly/lifetime) |
| 7-Day Free Trial | ✅ Complete | Standard tier trial |
| Milestone Action Cards | ✅ Complete | 15d/3d before templates + personalized suggestions |
| WeChat Subscribe Messages | ✅ Complete | Scheduler checks 15d/3d milestones daily |
| Quote Favorites | ✅ Complete | Add/remove favorites |
| Quote Share Image | ✅ Complete | Beautiful card image generation (Pillow) |
| Full Quote Library | ✅ Complete | 60 quotes (seeded), expandable |
| Knowledge Tree 3-Level | ✅ Complete | Full 365 nodes across 9 subjects |
| School Progress Tracking | ✅ Complete | CRUD with subject mapping |
| Score Trend Analysis | ✅ Complete | Exam score trend API |
| Growth Export PDF/Image | ✅ Complete | Long image generation |
| Desktop Shortcut Guide | ⏳ Phase 2 | Pending |

**Additional API Routers**:
- `subscription.py` — Subscription management, payment, trial
- `action_cards.py` — Action card templates + personalized display
- `school_progress.py` — School review progress CRUD

---

### Phase 3: AI Features 🚧 (In Progress)

| Feature | Status | Details |
|---------|--------|---------|
| AI Chat (家长顾问) | ✅ Complete | Conversational AI for parenting advice |
| Compliance Filter | ✅ Complete | Input/output filtering, blocks subject tutoring |
| LLM Client | ✅ Complete | OpenAI-compatible (DashScope, OpenAI, etc.) |
| AI Cost Control | ✅ Complete | Daily rate limits, token tracking, response caching |
| AI Monthly Report | ✅ Complete | AI-generated monthly growth reports |
| AI Action Suggestions | ✅ Complete | Personalized suggestions based on student data |
| AI Error Classification | ✅ Complete | Classify errors to knowledge points (no answers) |
| AI Chat Sessions | ✅ Complete | Conversation history with context management |
| AI Chat Frontend | ✅ Complete | Chat UI + history + monthly report + suggestions pages |

**AI Service Modules**:
- `llm_client.py` — Unified OpenAI-compatible async client
- `ai_chat_service.py` — Conversational AI with context & compliance
- `ai_quote_service.py` — AI-generated personalized quotes
- `ai_monthly_report_service.py` — Monthly growth report generation
- `ai_action_suggestion_service.py` — Personalized action recommendations
- `ai_error_classify_service.py` — Error note classification
- `compliance_filter.py` — Subject-tutoring content blocker
- `ai_cost_control.py` — Rate limiting, token tracking, caching

**AI-Specific API Routers**:
- `ai_chat.py` — Chat sessions, messages, streaming
- `ai_features.py` — Monthly reports, action suggestions, error classification

---

### Phase 4: Cross-Region Expansion (Planned)

| Feature | Status |
|---------|--------|
| Other provinces/cities | ⏳ Future |
| National college entrance exam support | ⏳ Future |

---

## 🔒 Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=dev
DB_PASSWORD=devpass
DB_NAME=gaokao_companion

# Test Database
TEST_DB_HOST=localhost
TEST_DB_PORT=5433
TEST_DB_USER=dev
TEST_DB_PASSWORD=devpass
TEST_DB_NAME=gaokao_companion_test

# JWT
JWT_SECRET=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRES_HOURS=168

# WeChat
WX_APP_ID=your-wechat-app-id
WX_APP_SECRET=your-wechat-app-secret

# WeChat Pay (V3)
WX_PAY_MCH_ID=
WX_PAY_API_KEY_PATH=
WX_PAY_CERT_PATH=
WX_PAY_NOTIFY_URL=

# Tencent Cloud COS
COS_BUCKET=your-bucket-name
COS_REGION=ap-shanghai
COS_SECRET_ID=your-secret-id
COS_SECRET_KEY=your-secret-key

# LLM / AI (DashScope / OpenAI-compatible)
LLM_PROVIDER=dashscope
LLM_API_KEY=
LLM_MODEL=qwen-turbo
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_DAILY_CHAT_LIMIT=10
AI_MAX_CONTEXT_ROUNDS=10

# Redis (optional)
REDIS_URL=

# App
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## 🤖 AI Features Detail

### AI 家长顾问 (AI Parental Advisor)
- Conversational AI that provides parenting advice (not subject tutoring)
- Context-aware: knows student's grade, subjects, current phase
- Strict compliance filter blocks all subject-related tutoring
- Daily chat limit (configurable, default 10 messages/day)
- Multi-turn conversation with context retention

### AI Monthly Report
- Auto-generated monthly growth report based on:
  - Score changes (exam data)
  - Error note trends
  - Growth records and highlights
  - Milestone completions
- Warm, encouraging tone — does not create anxiety
- Compliant: only data summaries and parental advice

### AI Action Suggestions
- Personalized suggestions based on:
  - Student grade and subject selection
  - Current academic phase
  - Error note distribution
  - Score trends
- 3-5 actionable suggestions with priority levels
- Categories: study rhythm, emotional support, time management, exam prep, daily life

### AI Error Classification
- Classifies error notes to knowledge points
- Does NOT provide answers or solutions
- Outputs: subject, chapter, knowledge points, difficulty assessment, study advice for parents

### Compliance System
- Input filtering: blocks questions about subject knowledge, problem-solving
- Output filtering: prevents AI from giving answers or step-by-step solutions
- System prompt enforcement: every AI call includes compliance rules
- Audit logging: all blocked requests are logged

---

## 📝 Documentation

- **Spec.md**: Full technical specification (16 tables, 25 pages, business rules)
- **Development-Plan.md**: Sprint breakdown, timeline, architecture decisions
- **Product Vision**: See `Analysis-folder/6.1 Production-vision 调整版5.1版`

---

## 🤝 Contributing

This is a solo project. For questions or suggestions, please open an issue on GitHub.

---

## 📄 License

TBD

---

## 📞 Contact

- GitHub: https://github.com/JaniceWei99/Gaokao-Review-New

---

**Current Version**: v0.2.0 (Phase 1 + 1.5 Complete, Phase 2 Mostly Complete, Phase 3 In Progress)
