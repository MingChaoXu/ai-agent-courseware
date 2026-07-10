# Context Compression Strategy Skill

## Description

上下文压缩策略实验 skill for TeleAgent.

Comparison topics: BufferMemory, SummaryMemory, 滑动窗口.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex3_5_context_compress_chat` | Ask about comparison topic | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex3_5_context_compress/skill ~/.config/TeleAgent/skills/ex3_5_context_compress
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
