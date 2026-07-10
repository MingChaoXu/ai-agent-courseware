# Event-Driven Agent Practice Skill

## Description

事件驱动Agent实战 skill for TeleAgent.

Multi-agent workflow: timer_agent, data_alert_agent, external_event_agent.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex15_5_event_driven_chat` | Run multi-agent workflow | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex15_5_event_driven/skill ~/.config/TeleAgent/skills/ex15_5_event_driven
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
