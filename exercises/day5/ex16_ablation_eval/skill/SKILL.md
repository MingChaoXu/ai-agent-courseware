# Agent Ablation Evaluation Skill

## Description

智能体消融评估 skill for TeleAgent.

Comparison topics: 完整Agent, 去除SystemPrompt, 去除工具描述, 非正式语气.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex16_ablation_eval_chat` | Ask about comparison topic | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex16_ablation_eval/skill ~/.config/TeleAgent/skills/ex16_ablation_eval
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
