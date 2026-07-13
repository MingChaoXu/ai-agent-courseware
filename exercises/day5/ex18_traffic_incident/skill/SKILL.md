# Traffic Incident Management Skill

## Description

交通事件智能处置Agent skill for TeleAgent. Provides 5-agent pipeline for traffic incident management: incident analysis, impact assessment (with AMap API), dispatch planning, multi-channel info publishing, and review report generation. Also includes incident database CRUD operations.

## Architecture

5-Agent sequential pipeline with AMap API enrichment:

```
User Input → Agent1(Incident Analysis)
           → [AMap API: Geocode + Around Search + Traffic + Routes]
           → Agent2(Impact Assessment)
           → Agent3(Dispatch Plan)
           → Agent4(Info Publish)
           → Agent5(Review Report)
```

## AMap API Integration

This skill integrates with AMap (高德地图) REST APIs. It works in two modes:

- **Online mode**: When `AMAP_API_KEY` is set in `.env`, calls real AMap APIs for geocoding, nearby facility search, real-time traffic, and driving route planning.
- **Offline mode**: When no key is configured, returns realistic mock data for testing and development.

## Tools

### AI Analysis Modules

| Tool | Description | Parameters |
|------|-------------|------------|
| `traffic_analyze` | Run full 5-agent pipeline on incident description | input_text (str) |
| `traffic_health_check` | Check agent health, AMap mode, and available modules | - |

### Incident Database Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `incident_list` | Query incident list, filterable by keyword and status | keyword (str), status (str) |
| `incident_detail` | Get incident details and dispatch records | incident_id (int) |

### AMap Query Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `amap_query_location` | Query location info: geocode, nearby facilities, traffic, routes | address (str) |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex18_traffic_incident/skill ~/.config/TeleAgent/skills/ex18_traffic_incident
```

## Configuration

Requires a `.env` file in the project root:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | LLM API key | Yes |
| `OPENAI_API_BASE` | LLM API base URL | Yes |
| `OPENAI_MODEL_NAME` | Model name | Yes |
| `AMAP_API_KEY` | AMap (高德地图) API key | No (offline mode if absent) |

## CLI Usage

```bash
# Full 5-agent pipeline
python skill/tools/tool.py analyze -q "三环路辅路与人民路交叉口发生多车追尾事故"

# Health check
python skill/tools/tool.py health

# Incident database
python skill/tools/tool.py incident-list --keyword 事故
python skill/tools/tool.py incident-detail --incident-id 1

# AMap location query
python skill/tools/tool.py amap-query --address "三环路辅路与人民路交叉口"
```
