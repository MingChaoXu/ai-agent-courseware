---
name: hr-review
description: "人事制度审查：5维度合规性分析+结构化输出"
name_cn: "人事制度智能审查"
description_cn: "人事制度审查：5维度合规性分析+结构化输出"
---
# HR Policy Intelligent Review Skill

## Description

人事制度智能审查 skill for TeleAgent.

Produces structured HRReviewResult output via PydanticOutputParser.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex7_hr_review_analyze` | Analyze input text | input_text (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex7_hr_review/skill ~/.config/TeleAgent/skills/ex7_hr_review
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
