# Governance Brief Generation - 政务通报智能生成

A full-stack AI agent project with FastAPI backend, Vue frontend, and TeleAgent skill integration.

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
| POST | /api/chat | Send question/request to agent |



## Project Structure

```
ex8_governance_brief/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── agent/
│   │   └── agent.py
│   ├── api/
│   │   ├── chat.py
│   │   └── health.py
│   ├── models/
│   │   └── schemas.py
│   └── requirements.txt
├── frontend/
│   └── index.html
├── data/
├── skill/
│   ├── SKILL.md
│   └── tools/
│       └── tool.py
├── .env.example
└── .gitignore
```

## Tech Stack

- **Backend**: FastAPI + LangChain 1.x
- **Frontend**: Vue 3 (CDN) + CSS
- **LLM**: OpenAI-compatible API
- **Skill**: Python module for TeleAgent integration
