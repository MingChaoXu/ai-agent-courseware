# Medical Record Structured Generation Skill

## Description

医疗病历结构化生成 skill for TeleAgent.

Produces structured MedicalRecord output via PydanticOutputParser.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex3_medical_record_analyze` | Analyze input text | input_text (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex3_medical_record/skill ~/.config/TeleAgent/skills/ex3_medical_record
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
