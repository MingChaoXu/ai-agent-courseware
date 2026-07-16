---
name: marketing-rfm
description: "精准营销：RFM客户分群+策略推荐"
name_cn: "精准营销RFM分析"
description_cn: "精准营销：RFM客户分群+策略推荐"
---
# Precision Marketing RFM Analysis Skill

## Description

精准营销RFM分析 skill for TeleAgent.

Produces structured CustomerProfile output via PydanticOutputParser.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex10_marketing_analyze` | Analyze input text | input_text (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex10_marketing/skill ~/.config/TeleAgent/skills/ex10_marketing
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
