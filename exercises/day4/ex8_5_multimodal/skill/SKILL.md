# Multimodal Processing Mode Comparison Skill

## Description

多模态处理三种模式对比 skill for TeleAgent.

Comparison topics: NATIVE模式, EXTRACT模式, TOOL模式.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex8_5_multimodal_chat` | Ask about comparison topic | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex8_5_multimodal/skill ~/.config/TeleAgent/skills/ex8_5_multimodal
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
