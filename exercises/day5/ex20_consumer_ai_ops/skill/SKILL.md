# Consumer AI Ops Skill

## Description

Consumer AI operations skill for TeleAgent. Provides 3 AI modules for consumer retail: BI analysis (ReAct Agent with data tools), customer service (RAG + multi-agent pipeline), and marketing strategy (RFM segmentation + persona + sentiment + campaign strategy + ROI Monte Carlo simulation).

## Architecture

Three independent AI engines, each demonstrating a different LangChain pattern:

```
Module 1: BI Analysis (ReAct Agent)
  User Question → create_react_agent(LLM, 4 tools)
    → query_sales / query_customers / calc_statistics / generate_chart
  → Natural language answer + optional ECharts spec

Module 2: Customer Service (RAG + Multi-Agent)
  User Question → Agent1(Intent Classification)
               → Agent2(RAG Retrieval from FAQ FAISS index)
               → Agent3(Answer Generation)
               → Agent4(Sentiment Analysis + Ticket Creation)

Module 3: Marketing (Structured Output + Computed)
  - RFM Segmentation (computed, no LLM)
  - Customer Persona (PydanticOutputParser → CustomerPersona)
  - Sentiment Analysis (PydanticOutputParser → SentimentReport)
  - Campaign Strategy (PydanticOutputParser → CampaignStrategy)
  - ROI Simulation (Monte Carlo, computed, no LLM)
```

## Tools

### BI Analysis

| Tool | Description | Parameters |
|------|-------------|------------|
| `consumer_bi_analyze` | Natural language BI analysis with ReAct Agent | question (str) |
| `consumer_bi_dashboard` | Get pre-computed BI dashboard data | - |

### Customer Service

| Tool | Description | Parameters |
|------|-------------|------------|
| `consumer_cs_chat` | Chat with AI customer service (RAG + multi-agent) | question (str), session_id (str) |
| `consumer_cs_faq` | Get FAQ list, optionally filtered by category | category (str) |
| `consumer_cs_stats` | Get customer service statistics | - |

### Marketing

| Tool | Description | Parameters |
|------|-------------|------------|
| `consumer_mk_segmentation` | Get RFM segmentation data | - |
| `consumer_mk_persona` | Generate customer persona (LLM-powered) | customer_id (str) |
| `consumer_mk_sentiment` | Analyze review sentiment by category (LLM-powered) | category (str) |
| `consumer_mk_strategy` | Generate campaign strategy (LLM-powered) | segment (str), objective (str) |
| `consumer_mk_simulate` | ROI Monte Carlo simulation | budget (float), target_segment (str), channel_mix (dict) |

### Health Check

| Tool | Description | Parameters |
|------|-------------|------------|
| `consumer_health_check` | Check LLM configuration and data status | - |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex20_consumer_ai_ops/skill ~/.config/TeleAgent/skills/ex20_consumer_ai_ops
```

## Configuration

Requires a `.env` file in the project root:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | LLM API key | Yes |
| `OPENAI_API_BASE` | LLM API base URL | Yes |
| `OPENAI_MODEL_NAME` | Model name | Yes |
| `EMBEDDING_MODEL_NAME` | Embedding model name | Yes (for CS RAG) |
| `EMBEDDING_API_KEY` | Embedding API key (defaults to OPENAI_API_KEY) | No |
| `EMBEDDING_API_BASE` | Embedding API base (defaults to OPENAI_API_BASE) | No |

## CLI Usage

```bash
# Health check
python skill/tools/tool.py health

# BI analysis
python skill/tools/tool.py bi -q "本月各区域销售对比"

# Customer service
python skill/tools/tool.py cs -q "如何退货退款"

# Marketing
python skill/tools/tool.py segmentation
python skill/tools/tool.py persona --customer-id C001
python skill/tools/tool.py sentiment
python skill/tools/tool.py strategy --segment "高价值沉睡" --objective "提升复购率"
python skill/tools/tool.py simulate --budget 100000
```
