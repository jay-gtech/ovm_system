# OVM System (Order & Vendor Management)

A production-grade financial control system with AI assistance.

## Phase 0: Foundation Setup

### Tech Stack
- **Backend:** FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2, PostgreSQL 16, Redis 7.
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS.
- **Infrastructure:** Docker Compose.

---

## Folder Structure

```text
ovm_system/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── core/         # Config, security, logging
│   │   ├── db/           # Session & Base models
│   │   ├── modules/      # Domain-specific modules (Modular Monolith)
│   │   ├── repositories/ # Data access layer
│   │   ├── schemas/      # Pydantic models
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI entry point
│   ├── alembic/          # Database migrations
│   ├── tests/            # Pytest suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── components/   # Shared UI components
│   │   ├── modules/      # Domain-specific UI logic
│   │   ├── services/     # API integration
│   │   ├── store/        # State management
│   │   └── App.tsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

---

## Installation & Setup

### 1. Infrastructure
Ensure Docker and Docker Compose are installed.

```bash
# Start PostgreSQL and Redis
docker-compose up -d
```

### 2. Backend Setup
Recommended: Use a virtual environment (Python 3.10+).

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run FastAPI
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Verification

- **Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Frontend:** [http://localhost:3000](http://localhost:3000)

---

## Architecture Rules

1. **Route → Service → Repository:** No database logic in routes.
2. **Async First:** All database and external calls must be async.
3. **Modular Monolith:** Organize code by domain in `app/modules`.
4. **Tenant Isolation:** Always consider `tenant_id` in queries (Future Phase).
