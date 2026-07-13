# 基层门诊AI辅助诊疗

A full-stack AI agent project with FastAPI backend, Vue frontend, SQLite patient database, and TeleAgent skill integration.

## Quick Start

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure API

```bash
cp .env.example .env
# Edit .env with your API key and base URL
```

### 3. Start the server

```bash
cd backend
python main.py
```

The API will be available at http://localhost:8000

API docs: http://localhost:8000/docs

### 4. Open the frontend

Open `frontend/index.html` in a browser, or access it through the FastAPI static file serving.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | System health check |
| POST | /api/chat | AI analysis (5 modules, optional patient archiving) |
| GET | /api/patients | List patients (with search) |
| POST | /api/patients | Create patient |
| GET | /api/patients/{id}/summary | Comprehensive patient summary |
| GET | /api/patients/{id}/visits | Get visit records |
| GET | /api/patients/{id}/vital-trends | Vital sign trends for charting |
| GET | /api/patients/{id}/medications | Medications list |
| GET | /api/patients/{id}/diagnoses | Diagnoses list |
| POST | /api/patients/vitals | Add vital sign |
| POST | /api/patients/medications | Add medication |
| POST | /api/patients/diagnoses | Add diagnosis |
| POST | /api/patients/timeline-analysis | AI timeline analysis |

## Project Structure

```
ex3_medical_record/
├── backend/
│   ├── main.py              # FastAPI entry, init agent + DB
│   ├── config.py            # Settings from .env
│   ├── agent/
│   │   └── agent.py         # 5 Pydantic models + LCEL Chains
│   ├── api/
│   │   ├── chat.py          # /api/chat + auto-extract logic
│   │   ├── health.py        # /api/health
│   │   └── patients.py      # Patient/Visit/Vital/Med/Diag CRUD + timeline
│   ├── db/
│   │   └── database.py      # SQLite 5 tables + seed data
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response
│   └── requirements.txt
├── frontend/
│   └── index.html           # Vue 3 SPA, 5 Tabs, SVG trend charts
├── data/                    # 8 test samples + patients.db
├── skill/
│   ├── SKILL.md
│   └── tools/
│       └── tool.py          # 11 tool functions (6 AI + 5 patient DB)
├── .env.example
└── .gitignore
```

## Tech Stack

- **Backend**: FastAPI + LangChain 1.x + SQLite
- **Frontend**: Vue 3 (CDN) + CSS + SVG charts
- **LLM**: OpenAI-compatible API
- **Database**: SQLite (5 tables, 16 vital metrics, zero-config)
- **Skill**: Python module for TeleAgent integration (11 tools)