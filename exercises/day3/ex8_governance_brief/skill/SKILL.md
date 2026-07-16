---
name: governance-brief
description: "政务通报生成：分类型规范化公文输出"
name_cn: "政务通报智能生成"
description_cn: "政务通报生成：分类型规范化公文输出"
---
# Governance Brief Generation Skill

## Description

政务通报智能生成 skill for TeleAgent.

Produces structured GovernanceBrief output via PydanticOutputParser.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex8_governance_brief_analyze` | Analyze input text | input_text (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex8_governance_brief/skill ~/.config/TeleAgent/skills/ex8_governance_brief
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
  python skill/tools/tool.py analyze -q 'input text'
  python skill/tools/tool.py health
```
