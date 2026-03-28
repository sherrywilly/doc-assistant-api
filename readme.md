# 📄 AI Document Assistant

A production-ready, microservice-based AI platform that lets you upload any PDF and chat with it in plain English. Built with FastAPI, Streamlit, LangChain, ChromaDB, Google Gemini, and JWT authentication.

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Browser / Client                     │
└──────────────┬──────────────────────────┬────────────┘
               │ :8501                    │ auth only
               ▼                          ▼
┌─────────────────────┐     ┌─────────────────────────┐
│  frontend           │     │  auth-service           │
│  Streamlit UI       │────▶│  FastAPI + SQLite       │
│  (port 8501)        │     │  JWT register / login   │
└────────┬────────────┘     │  (port 8001)            │
         │ Bearer JWT        └─────────────────────────┘
         ▼ :8000
┌─────────────────────┐
│  api-service        │
│  FastAPI + RAG      │
│  LangChain + Gemini │
│  ChromaDB vectors   │
│  (port 8000)        │
└─────────────────────┘
```

## 🚀 Quick Start — Docker Compose (recommended)

```bash
# 1. Clone
git clone https://github.com/sherrywilly/doc-assistant-api
cd doc-assistant-api

# 2. Create a .env file
cat > .env <<EOF
GOOGLE_API_KEY=your-gemini-api-key
JWT_SECRET_KEY=a-long-random-secret-at-least-32-chars
EOF

# 3. Start all three services
docker compose up --build

# 4. Open http://localhost:8501  (Streamlit UI)
#    API docs: http://localhost:8000/docs
#    Auth docs: http://localhost:8001/docs
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI |
| Auth | JWT (python-jose) + PBKDF2-SHA256 (passlib) |
| AI Orchestration | LangChain |
| Vector Store | ChromaDB |
| LLM | Google Gemini 2.0 Flash |
| Embeddings | Google Generative AI Embeddings |
| User Store | SQLite (via SQLAlchemy) |
| Frontend | Streamlit |
| Containerisation | Docker + Docker Compose |
| CI | GitHub Actions |
| Registry | GitHub Container Registry (GHCR) |

## ⚙️ Services

### auth-service (port 8001)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/register` | POST | Create an account |
| `/auth/login` | POST | Get a JWT token (OAuth2 form) |
| `/auth/verify` | POST | Validate a token |

### api-service (port 8000)
All document endpoints require a `Authorization: Bearer <token>` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/upload/{doc_id}` | POST | Upload & index a PDF |
| `/api/v1/ask/{doc_id}` | POST | Ask a question about a doc |
| `/api/v1/docs/list` | GET | List your uploaded documents |

### frontend (port 8501)
Full Streamlit UI with login/register, PDF upload, conversation history, export chat, and a per-user document library.

## 📁 Project Structure

```
doc-assistant-api/
├── app/                        # API service
│   ├── main.py
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── security.py         # JWT verification dependency
│   │   └── middleware.py       # Request logging middleware
│   ├── routes/
│   │   ├── document.py         # Upload / Ask / List endpoints
│   │   └── health.py           # Health endpoint
│   └── services/
│       └── rag.py              # LangChain RAG pipeline
├── auth_service/               # Auth microservice
│   ├── app/
│   │   ├── main.py             # Register / Login / Verify
│   │   ├── auth.py             # PBKDF2 hashing + JWT creation
│   │   ├── database.py         # SQLAlchemy + SQLite
│   │   ├── models.py           # User ORM model
│   │   └── schemas.py          # Pydantic schemas
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   ├── conftest.py             # Shared fixtures + auth override
│   ├── test_api.py             # API service tests (21 tests)
│   ├── test_auth.py            # Auth service tests (14 tests)
│   └── test_frontend.py        # Frontend tests (24 tests)
├── frontend.py                 # Streamlit app
├── Dockerfile                  # API service image
├── Dockerfile.frontend         # Frontend service image
├── docker-compose.yml          # 3-service orchestration
├── requirements.txt            # API service dependencies
└── .github/workflows/
    ├── ci.yml                  # Test + lint on every push/PR
    └── cd.yml                  # Build + push to GHCR on main
```

## 🔑 Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | api-service | Your Google Gemini API key |
| `JWT_SECRET_KEY` | api-service, auth-service | Shared JWT signing secret |
| `DATABASE_URL` | auth-service | SQLite URL (default: `sqlite:///./users.db`) |

## 🧪 Running Tests Locally

```bash
pip install -r requirements.txt
pip install -r auth_service/requirements.txt
pip install pytest httpx

GOOGLE_API_KEY=dummy JWT_SECRET_KEY=test python -m pytest tests/ -v
```

## 🔄 CI/CD

- **CI** (`.github/workflows/ci.yml`): Runs linting (`ruff`) and the full test suite on every push and pull request.
- **CD** (`.github/workflows/cd.yml`): Builds and pushes three Docker images to GHCR on every merge to `main`.

Images published:
- `ghcr.io/<owner>/doc-assistant-auth:latest`
- `ghcr.io/<owner>/doc-assistant-api:latest`
- `ghcr.io/<owner>/doc-assistant-frontend:latest`

## 💡 How RAG Works

```
User uploads PDF
      ↓
PDF split into 1000-char chunks (200 overlap)
      ↓
Chunks embedded with Google text-embedding-001
      ↓
Vectors stored in ChromaDB (per-user namespace)
      ↓
User asks a question
      ↓
ChromaDB retrieves most relevant chunks
      ↓
Gemini 2.0 Flash answers from context only
      ↓
Answer returned with full conversation history
```

## 👨‍💻 Author

**Sherry Wilson** — Python & AI Backend Developer
- LinkedIn: linkedin.com/in/sherry-wilson-python-dev
- GitHub: github.com/sherrywilly
