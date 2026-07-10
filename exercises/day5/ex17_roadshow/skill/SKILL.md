# Comprehensive Roadshow Agent Skill

## Description

综合方案路演Agent skill for TeleAgent.

Multi-agent workflow: scenario_agent, solution_agent, demo_agent, value_agent.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex17_roadshow_chat` | Run multi-agent workflow | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex17_roadshow/skill ~/.config/TeleAgent/skills/ex17_roadshow
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
  python skill/tools/tool.py chat -q 'your request'
  python skill/tools/tool.py health
```
