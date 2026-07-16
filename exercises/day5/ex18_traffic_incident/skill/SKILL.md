---
name: traffic-incident
description: "交通事件：5Agent串行+高德地图+警力调配"
name_cn: "交通事件智能处置Agent"
description_cn: "交通事件：5Agent串行+高德地图+警力调配"
---
# Traffic Incident Management Skill

## Description

交通事件智能处置Agent skill for TeleAgent. Provides:

1. **5-Agent Pipeline**: incident analysis, impact assessment (with AMap API), dispatch planning, multi-channel info publishing, and review report generation.
2. **Police Force Allocation**: real-time police unit distribution monitoring, optimal allocation algorithm, and allocation visualization.
3. **Personnel Database**: OA-style searchable personnel directory with stats, filtering, and unit lookup.
4. **Incident Database**: CRUD operations for incidents and dispatch records.

## Architecture

5-Agent sequential pipeline with AMap API enrichment + Police Force Allocation:

```
User Input → Agent1(Incident Analysis)
           → [AMap API: Geocode + Around Search + Traffic + Routes]
           → Agent2(Impact Assessment)
           → Agent3(Dispatch Plan)
           → Agent4(Info Publish)
           → Agent5(Review Report)
           → [Geocode incident location]
           → Police Allocation Algorithm (severity-based, distance/type/ETA)
```

The police allocation is triggered automatically after the 5-Agent pipeline completes geocoding the incident location.

## AMap API Integration

This skill integrates with AMap (高德地图) REST APIs. It works in two modes:

- **Online mode**: When `AMAP_API_KEY` is set in `.env`, calls real AMap APIs for geocoding, nearby facility search, real-time traffic, and driving route planning.
- **Offline mode**: When no key is configured, returns realistic mock data for testing and development.

## Police Force Allocation Algorithm

The `police_allocate` tool uses a greedy algorithm:

1. **Severity config**: 轻微(3人,1单位,交警), 一般(6人,2单位,交警), 严重(12人,3单位,交警+巡警), 特重大(20人,4单位,交警+特警+巡警)
2. **Filter**: units within response range × 1.3, status not "已调度"
3. **Rank**: type match priority → distance → ETA
4. **Greedy select**: pick units until personnel requirement + type coverage met
5. **Verify**: ensure all required unit types are covered

Distance is computed via Haversine formula on GCJ-02 coordinates. ETA model: base dispatch time (2-4min) + distance / type-specific speed (交警30km/h, 巡警28km/h, 特警40km/h, 派出所25km/h).

## Tools

### AI Analysis Modules

| Tool | Description | Parameters |
|------|-------------|------------|
| `traffic_analyze` | Run full 5-agent pipeline on incident description | input_text (str) |
| `traffic_health_check` | Check agent health, AMap mode, and available modules | - |

### Police Force Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `police_units` | Get all police units with location, type, personnel, status | - |
| `police_allocate` | Optimal police allocation for an incident | lng (float), lat (float), severity (str) |

### Personnel Database Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `police_personnel` | Search personnel (OA system): keyword, type, status, role filters | keyword (str), unit_type (str), status (str), role (str) |
| `police_personnel_stats` | Personnel summary: total count, by type/status/role | - |

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

# Police force
python skill/tools/tool.py police-units
python skill/tools/tool.py police-allocate --lng 104.048 --lat 30.648 --severity 严重

# Personnel database
python skill/tools/tool.py police-personnel --keyword 王
python skill/tools/tool.py police-personnel --unit-type 特警 --status 待命
python skill/tools/tool.py police-personnel-stats

# Incident database
python skill/tools/tool.py incident-list --keyword 事故
python skill/tools/tool.py incident-detail --incident-id 1

# AMap location query
python skill/tools/tool.py amap-query --address "三环路辅路与人民路交叉口"
```
