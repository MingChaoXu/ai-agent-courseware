---
name: bidding-assistant
description: "招投标：采集+LLM提取+客户匹配+Excel导出"
name_cn: "招投标助手"
description_cn: "招投标：采集+LLM提取+客户匹配+Excel导出"
---
# Bidding Assistant Skill

## Description

Bidding announcement collection and processing skill for TeleAgent. Provides a two-phase pipeline: Phase 1 collects bid announcements from 6 government/public procurement sources using Selenium, Phase 2 uses LLM (DeepSeek API) to extract structured fields (amount, category, deadlines, tenderer) and matches them against a customer list with similarity scoring.

## Architecture

```
Phase 1: Collection
  6 Selenium collectors (gov/gov2/jc/public/js/js2)
    → Merge → Deduplicate → Save JSON
    Output: data/phase1/phase1_collected_<timestamp>.json

Phase 2: Processing
  Read JSON → LLM Extract (DeepSeek API + CircuitBreaker)
    Fields: amount / is_it / public_due / result_due / tenderer
    → Customer Match (SequenceMatcher ≥ 0.70 + optional AI verify)
    → Export Excel
    Output: data/phase2/phase2_extracted_<timestamp>.xlsx
```

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `bidding_run_pipeline` | Run full pipeline (collect + process) | - |
| `bidding_run_phase1` | Run Phase 1 only (collect announcements) | - |
| `bidding_run_phase2` | Run Phase 2 only (LLM extract + customer match) | input_file (str, optional) |
| `bidding_search` | Keyword search across collected data | keyword (str), category (str, optional) |
| `bidding_list_files` | List Phase1/Phase2 output files | phase (str: phase1/phase2) |
| `bidding_health_check` | Check system health and component status | - |
| `bidding_get_config` | Get current configuration | - |

## Installation

```bash
# Symlink skill to TeleAgent skills directory
ln -s /path/to/ex21_bidding_assistant/skill ~/.config/TeleAgent/skills/bidding-assistant
```

## Configuration

Set in environment variables or `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `SILICONFLOW_API_KEY` | DeepSeek API key for LLM extraction | Yes |
| `HEADLESS` | Run Selenium in headless mode (1/0) | No |
| `CHROMEDRIVER_PATH` | Custom ChromeDriver path | No |
| `SILICONFLOW_VL_API_KEY` | Vision model key for screenshot OCR | No |

Also requires `kehu-0619.xlsx` in the `backend/` directory for customer matching.

## CLI Usage

```bash
# Health check
python tool.py health

# Run full pipeline
python tool.py pipeline

# Run Phase 1 only (collect)
python tool.py phase1

# Run Phase 2 only (process)
python tool.py phase2 --input data/phase1/phase1_collected_20260714_120000.json

# Search collected data
python tool.py search -k "市政工程"

# List files
python tool.py files --phase phase1
python tool.py files --phase phase2

# Get config
python tool.py config
```

## Python Import Usage

```python
from skill.tools.tool import (
    bidding_run_pipeline,
    bidding_run_phase1,
    bidding_run_phase2,
    bidding_search,
    bidding_list_files,
    bidding_health_check,
    bidding_get_config,
)

# Run full pipeline
result = bidding_run_pipeline()

# Search
results = bidding_search("市政工程")

# List Phase2 files
files = bidding_list_files("phase2")
```

## Data Sources

| Source | URL Pattern | Content |
|--------|------------|---------|
| gov | 苏州市政府采购平台 | 招标公告 |
| gov2 | 苏州市政府采购平台 | 采购意向 |
| jc | 金采平台 | 采购公告 |
| public | 公共资源平台 | 交易公告 |
| js | 江苏省政府采购平台 | 公开招标 |
| js2 | 江苏省政府采购平台 | 采购意向 |
