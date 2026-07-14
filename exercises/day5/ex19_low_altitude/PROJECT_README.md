# 低空智能体协同管控平台 - 开发者文档

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | Vue 3 (CDN) + Leaflet | 单HTML文件，无构建工具 |
| 后端 | FastAPI + uvicorn | Python异步API |
| LLM | LangChain + OpenAI兼容API | 多Agent编排 |
| CV | YOLOv8n (ultralytics) | 轻量目标检测模型 |
| 数据库 | SQLite | 零配置，内置种子数据 |
| 地图 | Leaflet + OpenStreetMap | 暗色主题 |

## 目录结构

```
ex19_low_altitude/
├── backend/
│   ├── main.py                 # FastAPI入口
│   ├── config.py               # 配置管理
│   ├── agent/
│   │   └── agent.py            # 多Agent编排核心
│   ├── api/
│   │   ├── chat.py             # 对话API
│   │   ├── health.py           # 健康检查
│   │   ├── drones.py           # 无人机管理API
│   │   ├── orders.py           # 物流订单API
│   │   ├── airspace.py         # 空域/事件/仪表盘API
│   │   └── cv.py               # CV检测API
│   ├── cv_service/
│   │   ├── yolo_server.py      # YOLO推理服务
│   │   └── detectors.py        # 检测逻辑(6种模式)
│   ├── db/
│   │   └── database.py         # SQLite CRUD
│   ├── models/
│   │   └── schemas.py          # Pydantic模型
│   └── data/
│       ├── low_altitude.db     # 运行时生成
│       └── test_images/        # 6张航拍测试图
├── frontend/
│   └── index.html              # Vue3单页应用
├── skill/
│   ├── SKILL.md                # 技能文档
│   └── tools/tool.py           # CLI + import工具
├── data/                       # 教学数据(.md)
│   ├── 01_airspace.md
│   ├── 02_orders.md
│   └── 03_scenarios.md
├── .env.example
├── .gitignore
├── EXERCISE.md                 # 学生任务
└── PROJECT_README.md           # 本文档
```

## 核心设计

### 1. 多Agent编排

采用 **Dispatcher路由模式**：

```python
# agent.py 核心流程
def chat(agent_data, question, force_agent=None):
    # 1. Dispatcher LLM判断路由
    agent_name = _dispatch(agent_data, question)

    # 2. CV决策：是否需要调用视觉检测
    cv_decision = _decide_cv_call(agent_name, question)

    # 3. 执行CV检测（如需要）
    cv_result = agent_cv_detect(cv_decision["detect_type"])

    # 4. 构建上下文（系统状态 + CV结果）
    full_input = f"{context}\n{question}\n{cv_context}"

    # 5. 执行Agent LLM
    answer = chains[agent_name].invoke({"input": full_input})

    # 6. 副作用处理（自动创建事件等）
    _process_side_effects(question, answer, cv_result)
```

### 2. CV服务设计

**一个YOLO模型，六种检测模式**：

```python
# detectors.py 核心逻辑
DETECT_CONFIG = {
    "aerial":   {"include_categories": None},           # 全量
    "obstacle": {"include_categories": {"obstacle", "vehicle"}},
    "intruder": {"include_categories": {"animal"}, "include_classes": {"bird", "airplane"}},
    "landing":  {"include_categories": {"human", "vehicle", "obstacle"}},
    "disaster": {"include_categories": None},
    "traffic":  {"include_categories": {"vehicle"}},
}
```

每种模式：
- 筛选不同类别的检测结果
- 评估威胁等级（normal/warning/danger）
- 生成自然语言分析报告
- 返回标注后的图片(base64)

### 3. Agent-CV协作流程

```
用户: "评估降落点安全性"
    ↓
Dispatcher → logistics
    ↓
CV决策: 检测到"降落"关键词 → landing模式
    ↓
YOLO推理 → 筛选人员/车辆/障碍物 → 威胁评估
    ↓
物流Agent: [系统状态 + CV结果 + 用户问题] → LLM
    ↓
输出: "降落区检测到5名行人、2辆车，威胁等级：危险，建议选择备用降落点"
```

### 4. 数据库设计

4张核心表 + 1张历史表：

| 表 | 说明 | 种子数据 |
|----|------|---------|
| drones | 6架无人机（鹰眼/猎鹰/信鸽/翼龙/蜂鸟/雷霆） | 不同状态/电量/位置 |
| orders | 3个物流订单（急救药品/文件快递/电子配件） | 不同优先级 |
| events | 3个活跃事件（航线偏离/天气预警/低电量） | 不同严重程度 |
| flight_paths | 2条飞行航线 | 含航点坐标 |
| chat_history | 对话历史 | 空 |

### 5. 前端布局

```
┌─────────────────────────────────────────────────┐
│                    顶部状态栏                      │
├──────────┬──────────────────────────────────────┤
│          │                                        │
│  对话面板  │            地图面板                    │
│  (380px)  │     (Leaflet + 无人机/事件标记)         │
│          │                                        │
│          ├──────────────────────────────────────┤
│          │         CV视觉面板 (280px)              │
│          │  ┌────────────┬───────────┐          │
│          │  │ 标注图片显示  │ 检测结果列表 │          │
│          │  └────────────┴───────────┘          │
└──────────┴──────────────────────────────────────┘
```

## API端点

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/chat` | 对话（支持agent参数指定Agent） |
| GET | `/api/health` | 健康检查 |
| GET | `/api/drones` | 无人机列表 |
| GET | `/api/orders` | 订单列表 |
| POST | `/api/orders` | 创建订单 |
| POST | `/api/orders/{id}/assign/{drone_id}` | 分配无人机 |
| GET | `/api/events` | 事件列表 |
| GET | `/api/flight-paths` | 航线列表 |
| GET | `/api/dashboard` | 仪表盘数据 |
| POST | `/api/cv/detect` | CV检测 |
| GET | `/api/cv/samples` | 测试图片列表 |
| GET | `/api/cv/status` | CV模型状态 |

## 快速启动

```bash
# 1. 进入项目目录
cd exercises/day5/ex19_low_altitude

# 2. 复制环境配置
cp .env.example .env
# 编辑 .env 填入LLM API信息

# 3. 安装依赖
cd backend
pip install -r requirements.txt

# 4. 启动服务
python main.py
# YOLOv8n首次运行自动下载(~6MB)

# 5. 打开浏览器
# http://localhost:8300/app
```

## YOLO模型说明

- **模型**：YOLOv8n（nano版本，约6MB）
- **预训练**：COCO 80类（人、车、鸟、飞机等）
- **设备**：默认CPU，支持CUDA
- **首次运行**：自动从Ultralytics下载权重文件
- **测试图片**：6张AI生成的航拍场景图（2048x2048）

## 扩展方向

1. **视频流检测**：替换单图为RTSP/WebRTC流，实现实时检测
2. **模型微调**：收集低空航拍数据微调YOLO，提升检测精度
3. **Agent图编排**：引入LangGraph StateGraph实现Agent间有向图通信
4. **3D空域**：集成Cesium实现三维空域可视化
5. **多机协同**：实现无人机集群的分布式任务分配算法
6. **数字孪生**：接入真实无人机SDK（DJI、PX4）实现数字孪生仿真