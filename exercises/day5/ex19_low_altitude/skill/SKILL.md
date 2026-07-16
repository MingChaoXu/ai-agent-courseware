---
name: low-altitude-agent
description: "低空管控：4Agent+YOLOv8 CV+地图可视化"
name_cn: "低空智能体协同管控"
description_cn: "低空管控：4Agent+YOLOv8 CV+地图可视化"
---
# Low-Altitude Agent Platform Skill

## Description
低空智能体协同管控平台 - Multi-Agent + YOLO CV platform for low-altitude economy, integrating airspace perception, drone logistics, traffic control, and emergency response.

## Architecture

```
User Input
    │
    ▼
┌─────────────┐
│  Dispatcher  │  ── routes to appropriate agent
└──────┬──────┘
       │
   ┌───┼───┬───────────┐
   ▼   ▼   ▼           ▼
┌─────┐┌──────┐┌──────┐┌──────────┐
│ Perc││ Log  ││ Traf ││ Emergency│
│ ept ││ ist  ││ fic  ││          │
│ ion ││ ics  ││      ││          │
└──┬──┘└──┬───┘└──┬───┘└────┬─────┘
   │      │       │         │
   └──────┴───┬───┴─────────┘
              ▼
    ┌──────────────────┐
    │  CV Service       │
    │  (YOLOv8n + API)  │
    └──────────────────┘
```

## Tools

| Tool | Description |
|------|-------------|
| `low_altitude_chat` | 多Agent对话，自动路由到感知/物流/管制/应急 |
| `low_altitude_cv_detect` | YOLOv8视觉检测，6种模式 |
| `low_altitude_status` | 查询系统状态（无人机/订单/事件） |

## Installation

```bash
# Symlink skill to TeleAgent skills directory
ln -s /path/to/ex19_low_altitude/skill ~/.config/TeleAgent/skills/low-altitude-agent
```

## Configuration

Set in `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | LLM API key | (required) |
| `OPENAI_API_BASE` | LLM API base URL | (required) |
| `OPENAI_MODEL_NAME` | Model name | gpt-4o-mini |
| `YOLO_MODEL` | YOLO model file | yolov8n.pt |
| `YOLO_DEVICE` | Inference device | cpu |
| `SERVER_PORT` | API server port | 8300 |

## CLI Usage

```bash
# Chat with the platform
python tool.py chat -q "报告当前空域态势"

# Force specific agent
python tool.py chat -q "评估降落点安全性" -a logistics

# Run CV detection
python tool.py cv -t traffic
python tool.py cv -t landing -s open_field

# Check system status
python tool.py status
```

## Python Import Usage

```python
from skill.tools.tool import low_altitude_chat, low_altitude_cv_detect, low_altitude_status

# Chat
result = low_altitude_chat("从天府广场发急救药品到龙泉驿")

# CV detect
result = low_altitude_cv_detect("aerial")

# Status
result = low_altitude_status()
```

## CV Detect Types

| Type | Description | Sample Image |
|------|-------------|--------------|
| `aerial` | 航拍目标全量检测 | urban_density.jpg |
| `obstacle` | 飞行障碍物识别 | construction_site.jpg |
| `intruder` | 空域入侵检测 | river_bridge.jpg |
| `landing` | 降落点安全评估 | open_field.jpg |
| `disaster` | 灾害场景分析 | construction_site.jpg |
| `traffic` | 地面交通监控 | city_intersection.jpg |
