# User Memory Management Agent Skill

## Description

用户记忆管理Agent skill for TeleAgent.

Multi-agent workflow: memory_agent, qa_agent, update_agent.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex3_8_user_memory_chat` | Run multi-agent workflow | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex3_8_user_memory/skill ~/.config/TeleAgent/skills/ex3_8_user_memory
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
