# Manufacturing BI Analysis Agent Skill

## Description

制造业BI分析Agent skill for TeleAgent.

ReAct Agent with tools: query_production_data, execute_code.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex9_manufacturing_bi_chat` | Ask the agent a question | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex9_manufacturing_bi/skill ~/.config/TeleAgent/skills/ex9_manufacturing_bi
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
