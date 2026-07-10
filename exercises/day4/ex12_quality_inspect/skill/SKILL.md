# PCB Quality Inspection Agent Skill

## Description

PCB质量AI检测Agent skill for TeleAgent.

ReAct Agent with tools: defect_detect, ocr_extract, component_count.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex12_quality_inspect_chat` | Ask the agent a question | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex12_quality_inspect/skill ~/.config/TeleAgent/skills/ex12_quality_inspect
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
