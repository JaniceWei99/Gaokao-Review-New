# 上海高考复习助手 (Shanghai Gaokao Companion)

一款面向上海高中生家长的微信小程序，通过里程碑驱动的行动提醒、每日励志金句、错题拍照归档和孩子成长记录，帮助家长在高考备考全程中不焦虑、不缺席、不越界。

A WeChat mini-program for parents of Shanghai high school students, providing milestone-driven action reminders, daily inspirational quotes, error note photo archival, and growth records to help parents stay calm, present, and supportive during Gaokao preparation.

---

## 📋 Project Overview

### 一句话描述
纯家长端工具，孩子无需任何操作。家长通过里程碑时间提醒、通用行动建议、金句、错题拍照归档（不解题）、成长记录来陪伴孩子备考。

A parent-only tool requiring no action from the child. Parents use milestone reminders, action suggestions, quotes, error note archival (without solutions), and growth records to accompany their child's exam preparation.

### 目标用户
- 上海高一至高三考生家长（40-50岁）
- 熟练使用微信但不擅长复杂App

Shanghai high school student parents (ages 40-50), familiar with WeChat but not complex apps.

### 合规红线
- ❌ 不得提供学科知识点讲解、题目解答、解题过程
- ❌ 不得提供拍照搜题、题库练习、作业批改功能
- ❌ 不得推荐付费教师、课程或培训机构
- ❌ 不得生成"每日复习计划""个性化复习任务"等学科辅导内容
- ✅ 可以提供里程碑时间提醒、通用行动建议、金句、错题拍照归档（不解题）、成长记录

Compliance constraints: No subject instruction, problem solutions, homework grading, paid teacher recommendations, or personalized study plans. Milestone reminders, action suggestions, quotes, error note archival (without solutions), and growth records are allowed.

---

## 🏗️ Architecture

### Tech Stack

| Component | Technology | Rationale |
|-----------|-------------|-----------|
| **Frontend** | WeChat Mini Program (WXML + WXSS + JS) | Native WeChat ecosystem, no app installation |
| **Backend** | Python FastAPI | Auto Swagger docs, Pydantic validation, AI-ready for Phase 3 |
| **Database** | PostgreSQL 15+ | JSONB for milestone filtering, native ARRAY types |
| **ORM** | SQLAlchemy 2.0 | Modern async support, type-safe |
| **Migration** | Alembic | Database version control |
| **Scheduler** | APScheduler (Phase 1) → Celery+Redis (Phase 2) | Task scheduling for daily quotes & reminders |
| **Storage** | Tencent Cloud COS | Image storage for error notes |
| **Deployment** | Docker Compose (local) / Tencent Cloud (prod) | Containerized, cloud-native |
| **Auth** | WeChat Login (wx.login) + JWT | Seamless WeChat integration |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WeChat Mini Program                       │
│              (WXML / WXSS / JavaScript)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS (RESTful JSON)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │  API Routes │  │  Services  │  │  APScheduler       │    │
│  │  (Routers)  │  │  (Business) │  │  (Daily quotes,    │    │
│  │             │  │            │  │   reminders)       │    │
│  └──────┬─────┘  └──────┬─────┘  └────────────────────┘    │
│         │               │                                 │
│  ┌──────┴───────────────┴──────────┐                       │
│  │         SQLAlchemy ORM           │                       │
│  └──────────────┬──────────────────┘                       │
└─────────────────┼──────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│  PostgreSQL   │    │ Tencent COS  │
│  (16 tables)  │    │ (Images)     │
└──────────────┘    └──────────────┘
```

---

## 📁 Directory Structure

```
Gaokao-review-new/
├── Analysis-folder/          # Product vision iterations
├── Implementation/
│   ├── Spec.md               # Full technical specification (16 tables, 25 pages)
│   └── Development-Plan.md   # Sprint breakdown, timeline
├── miniprogram/              # WeChat mini-program frontend
│   ├── app.js/json/wxss     # App entry & global styles
│   ├── pages/                # 26 pages (104 files: .js/.json/.wxml/.wxss)
│   │   ├── onboarding/      # Welcome, grade select, subject select...
│   │   ├── index/           # Home page
│   │   ├── milestones/      # Timeline, action card, add custom
│   │   ├── exams/           # List, add, trend
│   │   ├── errors/          # List, add, detail
│   │   ├── growth/          # Timeline, add, export
│   │   ├── quotes/          # Favorites
│   │   ├── knowledge/       # Browse
│   │   └── profile/         # Settings, student manage, subscription
│   ├── services/            # API wrapper, auth
│   ├── utils/               # Date, storage helpers
│   └── constants/           # Subjects, districts, plans
├── server/                   # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry (health endpoint, CORS, error handlers)
│   │   ├── config.py        # Settings (pydantic-settings)
│   │   ├── database.py      # Async engine & session
│   │   ├── models/          # 16 SQLAlchemy 2.0 models
│   │   ├── schemas/         # 10 Pydantic v2 schema files (35 schemas)
│   │   ├── middleware/      # Auth, error handler, permission checker
│   │   ├── routers/         # API routes (Phase 1)
│   │   ├── services/        # Business logic (Phase 1)
│   │   └── utils/           # Helpers
│   ├── migrations/          # Alembic migrations
│   │   ├── env.py           # Migration config (imports all models)
│   │   └── versions/        # Migration files
│   ├── seeds/               # Reference data JSON
│   │   ├── subjects.json
│   │   ├── knowledge_tree/  # 9 subject JSON files (365 nodes)
│   │   ├── milestones.json  # 35 system milestones
│   │   ├── action_cards.json # 8 action card templates
│   │   └── quotes.json      # 60 daily quotes
│   ├── seed.py              # Seed import script
│   ├── requirements.txt     # Python dependencies
│   ├── pyproject.toml       # pytest config
│   └── alembic.ini          # Alembic config
├── docker-compose.yml       # PostgreSQL dev + test
├── Makefile                 # Common commands
├── .env.example             # Environment template
├── .github/workflows/ci.yml # GitHub Actions CI
└── README.md                # This file
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
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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
```

### Using Makefile

```bash
# Start/stop services
make dev-up
make dev-down

# Run tests
make test

# Run seed
make seed

# Migration
make migrate-up
make migrate-down
```

---

## 🧪 Testing

```bash
cd server
pytest tests/ -v
```

Current test coverage: 7 unit tests (health check, auth token creation/decoding).

---

## 📊 Database Schema

### 16 Tables

| Table | Rows (seeded) | Description |
|-------|---------------|-------------|
| subjects | 9 | 3 required + 6 elective subjects |
| knowledge_nodes | 365 | 3-level knowledge tree (9 subjects) |
| milestones | 35 | System milestones (2025-2026 school year) |
| action_cards | 8 | Action card templates |
| daily_quotes | 60 | Inspirational quotes (8 categories) |
| users | 0 | Parent accounts (created on WeChat login) |
| students | 0 | Child profiles (created during onboarding) |
| exams | 0 | Exam records |
| exam_scores | 0 | Exam scores per subject |
| error_notes | 0 | Error note photos |
| growth_records | 0 | Growth timeline records |
| user_quote_favorites | 0 | Favorited quotes |
| user_quote_history | 0 | Quote display history |
| milestone_reminders | 0 | User-specific reminder settings |
| school_progress | 0 | School progress tracking |
| user_subscriptions | 0 | Subscription plans |

See `Implementation/Spec.md` for detailed table definitions.

---

## 📈 Development Progress

### Phase 0: Infrastructure Scaffolding ✅ (Complete)

**Status**: v0.0.1 (phase0 ready)

**Completed**:
- ✅ FastAPI server with health endpoint, CORS, global error handlers
- ✅ 16 SQLAlchemy 2.0 models with full relationships & indexes
- ✅ Alembic migration (initial schema, all 16 tables)
- ✅ 10 Pydantic v2 request/response schemas (35 schemas total)
- ✅ JWT auth middleware + permission checker
- ✅ Seed data: 9 subjects, 365 knowledge nodes, 35 milestones, 8 action cards, 60 daily quotes
- ✅ WeChat mini-program skeleton: 26 pages, services, utils, constants
- ✅ Docker Compose (PostgreSQL 15 dev + test)
- ✅ GitHub Actions CI, Makefile, pytest (7 tests passing)
- ✅ Spec.md + Development-Plan.md

**Commit**: `0dde5ce` - 194 files, 16,181 insertions

### Phase 1: Core MVP (Planned)

**Estimated**: Weeks 3-8

**Planned features**:
- WeChat login integration
- Student profile CRUD
- Milestone timeline display
- Daily quote display
- Dashboard with countdowns

**API routers to implement**:
- `auth.py` - WeChat login, token refresh
- `student.py` - Student CRUD, onboarding flow
- `milestone.py` - Milestone listing, reminder settings
- `quote.py` - Daily quote, favorites
- `dashboard.py` - Aggregated dashboard data

See `Implementation/Development-Plan.md` for detailed Sprint breakdown.

### Phase 1.5: Error Notes + Growth Records (Planned)

**Estimated**: Weeks 9-12

### Phase 2: Monetization + Complete Features (Planned)

**Estimated**: Weeks 13-20

### Phase 3: AI Features (Planned)

**Estimated**: Weeks 21-28

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
WX_APP_ID=
WX_APP_SECRET=

# Tencent Cloud COS
COS_BUCKET=
COS_REGION=ap-shanghai
COS_SECRET_ID=
COS_SECRET_KEY=

# App
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
```

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

**Phase 0 Status**: ✅ Complete (v0.0.1)
