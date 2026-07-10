# Construction Document Generation Skill

## Description

施工文档智能生成 skill for TeleAgent.

Generates structured documents from input parameters.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex6_construction_doc_chat` | Generate document from input | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex6_construction_doc/skill ~/.config/TeleAgent/skills/ex6_construction_doc
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
  python skill/tools/tool.py chat -q 'project info'
  python skill/tools/tool.py health
```
