# Gov QA - Government Services Intelligent QA Agent

A full-stack RAG-based government services QA system with FastAPI backend, Vue frontend, and TeleAgent skill integration.

## Architecture

```
User Question
      │
      ▼
┌─────────────┐     ┌──────────────┐
│  Vue Frontend │────▶│  FastAPI Backend │
└─────────────┘     └──────────────┘
                           │
                    ┌──────┴──────┐
                    │  RAG Chain  │
                    └──────┬──────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
          ┌─────┴─────┐ ┌──┴──┐ ┌───┴────┐
          │ FAISS + KB │ │ LLM │ │ Prompt │
          └───────────┘ └─────┘ └────────┘
```

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

Open `frontend/index.html` in a browser, or access it through the FastAPI static file serving (after building).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | System health check |
| POST | /api/chat | Ask a question |
| DELETE | /api/chat/{id} | Clear conversation |
| GET | /api/knowledge | List knowledge base docs |
| POST | /api/knowledge/upload | Upload text content |
| POST | /api/knowledge/upload-file | Upload a file (.txt/.md/.json) |
| POST | /api/knowledge/search | Search knowledge base |
| POST | /api/knowledge/reload | Reload default data |

## Skill Integration

The `skill/` directory contains a TeleAgent-installable skill:

```python
from tools.gov_qa import GovQATool

tool = GovQATool()
tool.initialize()
answer = tool.run("新生儿落户需要什么材料？")
```

CLI usage:

```bash
cd skill
python -m tools.gov_qa answer -q "社保怎么转？"
python -m tools.gov_qa search --query "公积金贷款"
python -m tools.gov_qa init
```

## Project Structure

```
gov-qa/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration management
│   ├── agent/
│   │   ├── rag_chain.py     # RAG Chain (LangChain LCEL)
│   │   ├── knowledge_base.py # FAISS vector KB manager
│   │   └── prompts.py       # Prompt templates
│   ├── api/
│   │   ├── chat.py          # Chat endpoints
│   │   ├── knowledge.py     # Knowledge management
│   │   └── health.py        # Health check
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── requirements.txt
├── frontend/
│   └── index.html           # Vue 3 SPA (CDN)
├── data/
│   └── gov_faq.json         # 50 government FAQs
├── skill/
│   ├── SKILL.md             # Skill description
│   └── tools/
│       └── gov_qa.py        # TeleAgent tool
├── .env.example
└── .gitignore
```

## Tech Stack

- **Backend**: FastAPI + LangChain 1.x + FAISS
- **Frontend**: Vue 3 (CDN) + CSS
- **LLM**: OpenAI-compatible API
- **Embedding**: OpenAI Embeddings + FAISS
- **Skill**: Python module for TeleAgent integration