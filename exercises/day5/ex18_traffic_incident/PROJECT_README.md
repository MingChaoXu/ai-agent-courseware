# 交通事件智能处置Agent

## 项目说明

5个Agent协作处理交通事件（感知→评估→方案→发布→复盘），集成高德地图API实现在线/离线双模式。本文件是代码实现的技术文档，包含架构设计、API说明和代码细节。

## 项目结构

```
ex18_traffic_incident/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── agent/agent.py              # 5个Agent Chain + chat()流水线
│   ├── api/chat.py                 # 5Agent分析接口
│   ├── api/health.py               # 健康检查
│   ├── api/incidents.py            # 事件CRUD + 处置记录
│   ├── services/amap_client.py     # 高德API客户端（在线/离线）
│   ├── models/schemas.py
│   └── db/database.py              # SQLite（incidents + dispatches）
├── frontend/
│   └── index.html                  # Vue 3 CDN 单页应用
├── skill/
│   ├── SKILL.md
│   └── tools/tool.py
├── data/                           # 测试数据（5个交通事件样本）
├── EXERCISE.md
├── PROJECT_README.md
└── .env.example
```

## 后端架构

### 多Agent串行流水线

`create_agent()`返回包含5条独立LCEL Chain的字典和AMapClient实例：

- `incident_analysis`: 事件感知与分类（提取类型/位置/严重程度/紧急程度）
- `impact_assessment`: 影响范围评估（**注入高德API实时数据**）
- `dispatch_plan`: 疏导与救援方案（分流路线/资源调度/处置时序/协同单位）
- `info_publish`: 多渠道信息发布（广播/APP/情报板/社交媒体/内部通报）
- `review_report`: 事件复盘报告（概述/回顾/评估/经验/改进/预警）

**执行流程**：`chat()`函数串行调用5条Chain，中间调用AMapClient增强上下文：

```
用户输入 → Agent1(事件分析)
        → [从Agent1输出提取位置]
        → AMapClient.query_location_info(location)
          → geocode + around_search + traffic_status + driving_direction
        → Agent2(影响评估, 注入amap_data)
        → Agent3(疏导方案, 注入detour_routes)
        → Agent4(信息发布)
        → Agent5(复盘报告)
```

每条Chain独立try/except，单个Agent失败不阻塞后续Agent。

### 高德API客户端 (services/amap_client.py)

`AMapClient`类封装高德地图REST API，支持在线/离线双模式：

| 方法 | 功能 | 在线模式 | 离线模式 |
|------|------|----------|----------|
| `geocode(address)` | 地理编码 | 调用`/v3/geocode/geo` | 返回预置坐标 |
| `around_search(location, categories)` | 周边搜索 | 调用`/v3/place/around` | 返回预置POI |
| `traffic_status(location)` | 实时路况 | 调用`/v3/traffic/status/circle` | 返回预置路况 |
| `driving_direction(origin, dest)` | 路径规划 | 调用`/v3/direction/driving` | 返回预置路线 |
| `query_location_info(address)` | 一键综合查询 | 以上4个API组合调用 | 以上4个mock组合 |

**模式切换**：`is_online = bool(AMAP_API_KEY)`，在config.py中读取环境变量自动判断。

**POI类型映射**：
- hospitals → 090100（综合医院）
- fire_stations → 050301（消防）
- traffic_police → 050300（交通管理）
- gas_stations → 010100（加油站）

### API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查（返回amap_mode和5个模块列表） |
| POST | /api/chat | 5Agent分析（自动归档事件+处置记录） |
| GET | /api/incidents | 事件列表（支持keyword/status筛选） |
| POST | /api/incidents | 创建事件 |
| GET | /api/incidents/{id} | 事件详情 |
| PUT | /api/incidents/{id} | 更新事件 |
| DELETE | /api/incidents/{id} | 删除事件（级联删除处置记录） |
| GET | /api/incidents/{id}/dispatches | 处置记录列表 |
| POST | /api/incidents/dispatches | 添加处置记录 |
| DELETE | /api/incidents/dispatches/{id} | 删除处置记录 |

### 关键文件说明

- `agent/agent.py`: 5个Agent Chain定义 + `chat()`串行流水线 + AMap数据注入逻辑
- `services/amap_client.py`: 高德API客户端，封装5个REST接口 + 离线mock数据
- `api/chat.py`: 对话接口，调用agent_chat并自动归档到SQLite
- `api/incidents.py`: 事件CRUD + 处置记录管理
- `db/database.py`: SQLite（incidents + dispatches两表）+ seed预置5个交通事件
- `models/schemas.py`: Pydantic请求/响应模型
- `config.py`: LLM配置 + AMAP_API_KEY配置 + amap_mode属性
- `main.py`: FastAPI入口，注册路由、初始化Agent和数据库

## 前端说明

Vue 3 CDN单页应用，两个Tab页：

**Tab1 - 事件处置**：
- 5个样本快速选择卡片（交通事故/设施故障/危化品/暴雨/施工）
- 输入框 → 5个Agent结果分区展示（步骤编号+标题+内容）
- 高德API数据面板（地理编码/周边设施/实时路况/分流路线）
- 高德在线/离线模式状态指示

**Tab2 - 事件档案**：
- 事件列表（支持关键词搜索+状态筛选）
- 事件详情（基本信息+AI分析摘要）
- 处置记录查看（分析/方案/发布/复盘）

## Skill说明

封装为6个tool函数：
- `traffic_analyze`: 完整5-Agent流水线
- `traffic_health_check`: 健康检查（含amap_mode）
- `incident_list` / `incident_detail`: 事件数据库查询
- `amap_query_location`: 高德位置信息查询

## 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env填入LLM API配置
# 可选：填入AMAP_API_KEY启用高德在线模式（不填则使用离线模拟数据）

# 2. 安装依赖
pip install langchain langchain-openai python-dotenv fastapi uvicorn

# 3. 启动后端
cd backend
python main.py
# 访问 http://localhost:8000
```

## 技术栈

- **LLM框架**: LangChain 1.x（LCEL Chain）
- **外部API**: 高德地图REST API（地理编码/周边搜索/路况/路径规划）
- **后端**: FastAPI + Uvicorn + SQLite
- **前端**: Vue 3 (CDN)
- **LLM接口**: OpenAI兼容协议