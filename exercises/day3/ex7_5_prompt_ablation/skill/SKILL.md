# Prompt Ablation Experiment Skill

## Description

Prompt消融实验 skill for TeleAgent.

Comparison topics: 完整Prompt, 无角色设定, 无Few-shot, 无格式约束.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `ex7_5_prompt_ablation_chat` | Ask about comparison topic | question (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex7_5_prompt_ablation/skill ~/.config/TeleAgent/skills/ex7_5_prompt_ablation
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
