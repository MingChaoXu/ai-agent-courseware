---
name: industrial-kb
description: "工业运维RAG：FAISS向量检索+多轮问答"
name_cn: "工业运维知识库"
description_cn: "工业运维RAG：FAISS向量检索+多轮问答"
---
# Industrial Maintenance Knowledge Base Skill

## Description

工业运维知识库 skill for TeleAgent.

RAG with FAISS vector store. Data: industrial_kb.json.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex2_industrial_kb_chat` | Ask a question using RAG | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex2_industrial_kb/skill ~/.config/TeleAgent/skills/ex2_industrial_kb
```

## Configuration

Requires a `.env` file in the project root:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | LLM API key |
| `OPENAI_API_BASE` | LLM API base URL |
| `OPENAI_MODEL_NAME` | Model name |

## CLI Usage

```bash
  python skill/tools/tool.py chat -q 'your question'
  python skill/tools/tool.py health
```
