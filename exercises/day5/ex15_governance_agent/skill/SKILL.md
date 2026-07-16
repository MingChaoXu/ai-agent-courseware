---
name: governance-agent
description: "社会治理：4Agent并行+条件分支"
name_cn: "社会治理综合智能体"
description_cn: "社会治理：4Agent并行+条件分支"
---
# Social Governance Multi-Agent Skill

## Description

社会治理综合智能体 skill for TeleAgent.

Multi-agent workflow: event_entry_agent, legal_consultation_agent, brief_generation_agent, alert_agent.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex15_governance_agent_chat` | Run multi-agent workflow | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex15_governance_agent/skill ~/.config/TeleAgent/skills/ex15_governance_agent
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
