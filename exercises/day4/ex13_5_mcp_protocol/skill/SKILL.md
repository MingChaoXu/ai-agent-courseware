---
name: mcp-protocol
description: "MCP协议：感知/执行/协作三类工具演示"
name_cn: "MCP工具协议演示Agent"
description_cn: "MCP协议：感知/执行/协作三类工具演示"
---
# MCP Protocol Demo Agent Skill

## Description

MCP工具协议演示Agent skill for TeleAgent.

ReAct Agent with tools: web_search, code_execute, send_notification.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex13_5_mcp_protocol_chat` | Ask the agent a question | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex13_5_mcp_protocol/skill ~/.config/TeleAgent/skills/ex13_5_mcp_protocol
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
