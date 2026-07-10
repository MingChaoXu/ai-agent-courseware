# RAG Principle Deep Dive Skill

## Description

RAG原理深入实验 skill for TeleAgent.

Comparison topics: 稀疏检索(BM25), 稠密检索, 混合检索.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex2_5_rag_deep_chat` | Ask about comparison topic | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex2_5_rag_deep/skill ~/.config/TeleAgent/skills/ex2_5_rag_deep
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
