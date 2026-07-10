# Power Safety CV Inspection Agent Skill

## Description

电力安全CV检测Agent skill for TeleAgent.

ReAct Agent with tools: ppe_check, distance_check, environment_check.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex13_cv_safety_chat` | Ask the agent a question | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex13_cv_safety/skill ~/.config/TeleAgent/skills/ex13_cv_safety
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
