# ReAct Reasoning Principle Skill

## Description

ReAct推理原理实验 skill for TeleAgent.

ReAct Agent with tools: search_policy, calculate.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex0_react_principle_chat` | Ask the agent a question | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex0_react_principle/skill ~/.config/TeleAgent/skills/ex0_react_principle
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
