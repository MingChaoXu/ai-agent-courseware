# Government Services QA Skill

## Description

A RAG-based government services question answering skill for TeleAgent. Uses FAISS vector knowledge base + LangChain RAG chain to provide accurate, evidence-based answers to citizen questions.

Covers: household registration (户籍), social security (社保), housing provident fund (公积金), residence permit (居住证), property registration (不动产), and more.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `gov_qa_answer` | Answer a question using RAG | `question` (str), `conversation_id` (str, optional) |
| `gov_qa_search` | Search the knowledge base | `query` (str), `top_k` (int, default 5) |
| `gov_qa_upload` | Upload text content to KB | `title` (str), `content` (str) |
| `gov_qa_upload_file` | Upload a file to KB | `file_path` (str, supports .txt/.md/.json) |
| `gov_qa_list` | List all documents in KB | none |
| `gov_qa_clear` | Clear conversation history | `conversation_id` (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
# Option A: symlink (recommended)
ln -s /path/to/ex1_gov_qa/skill ~/.config/TeleAgent/skills/gov_qa

# Option B: copy
cp -r /path/to/ex1_gov_qa/skill ~/.config/TeleAgent/skills/gov_qa
```

## Configuration

Requires a `.env` file in the project root (`ex1_gov_qa/`):

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | LLM API key |
| `OPENAI_API_BASE` | LLM API base URL |
| `OPENAI_MODEL_NAME` | Model name |
| `EMBEDDING_MODEL_NAME` | Embedding model name |
| `EMBEDDING_API_KEY` | Embedding API key |
| `EMBEDDING_API_BASE` | Embedding API base URL |

## Test Data

| File | Description |
|------|-------------|
| `data/gov_faq.json` | 50 real government FAQs (10 categories), auto-loaded on startup |
| `data/test_户政业务网上办理指引.md` | Household registration online guide (Guangzhou Panyu) |
| `data/test_居住证申领指南.md` | Residence permit application guide (Liangshan) |
| `data/test_住房公积金贷款指南.md` | Housing fund loan guide (Shaoguan) |
| `data/test_社会保险参保办事指南.md` | Social insurance guide (Huaibei Xiangshan) |

## CLI Usage

```bash
# Initialize the knowledge base
python skill/tools/gov_qa.py init

# Ask a question
python skill/tools/gov_qa.py answer -q "新生儿落户需要什么材料？"

# Search the knowledge base
python skill/tools/gov_qa.py search --query "公积金贷款"

# List all documents
python skill/tools/gov_qa.py list

# Upload a file
python skill/tools/gov_qa.py upload-file -f data/test_居住证申领指南.md

# Check health status
python skill/tools/gov_qa.py health

# Clear conversation history
python skill/tools/gov_qa.py clear -c conv_123
```

## Architecture

```
User Question
    │
    ▼
┌──────────────────┐
│  FAISS Retriever  │ ── Top-K similar documents
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  RAG Prompt       │ ── Inject context + history + question
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  LLM (Chat)       │ ── Generate answer from context only
└──────────────────┘
    │
    ▼
Answer + Sources
```

## Relationship with Backend

The skill tool (`skill/tools/gov_qa.py`) reuses the backend (`backend/`) core modules directly:
- `agent/knowledge_base.py` — FAISS vector store management
- `agent/rag_chain.py` — RAG retrieval chain
- `agent/prompts.py` — System prompt template
- `config.py` — Environment configuration

The backend provides a Web API (FastAPI + Vue frontend), while the skill provides a TeleAgent tool interface. Both share the same RAG engine.
