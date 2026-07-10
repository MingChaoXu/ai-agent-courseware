# Government Service Full-Chain Agent Skill

## Description

政务服务全链路Agent skill for TeleAgent.

Multi-agent workflow: qa_agent, recommendation_agent, form_filling_agent, verification_agent, review_agent.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex14_gov_service_chat` | Run multi-agent workflow | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex14_gov_service/skill ~/.config/TeleAgent/skills/ex14_gov_service
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
