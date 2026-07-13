## 课题名称

交通事件智能处置Agent

## 学习目标

- 掌握多Agent串行协作架构，实现交通事件全链路智能处置（感知→评估→方案→发布→复盘）
- 理解外部API（高德地图）与LLM Agent的集成模式，实现在线/离线双模式切换

## 项目概述

5个Agent协作处理交通事件：incident_analysis(事件感知) + impact_assessment(影响评估，注入高德API数据) + dispatch_plan(疏导方案) + info_publish(信息发布) + review_report(复盘报告)。支持高德地图API在线模式（地理编码、周边搜索、实时路况、路径规划）和离线模式（模拟数据），构建FastAPI后端 + Vue前端的完整全栈项目。

## 任务要求

### 步骤1：实现高德API客户端（services/amap_client.py）

  - `geocode()`: 地址→经纬度（地理编码）
  - `around_search()`: 周边搜索（医院/消防/交警/加油站）
  - `traffic_status()`: 实时路况查询
  - `driving_direction()`: 驾车路径规划（分流路线）
  - 实现`is_online`属性检测：有AMAP_API_KEY走在线，无Key走离线模拟数据

### 步骤2：定义5个Agent的LCEL Chain（agent/agent.py）

  - `incident_analysis`: 事件感知与分类（类型/位置/严重程度/紧急程度）
  - `impact_assessment`: 影响范围评估（注入高德API返回的实时数据）
  - `dispatch_plan`: 疏导与救援方案（分流路线、资源调度、处置时序）
  - `info_publish`: 多渠道信息发布（广播/APP/情报板/社交媒体/内部通报）
  - `review_report`: 事件复盘报告（概述/回顾/评估/经验/改进/预警）

### 步骤3：实现chat()函数串行调用5条Chain

- chat()函数依次调用5条Chain，中间调用AMapClient增强上下文
- 执行流程：Agent1(分析) → [AMap查询位置] → Agent2(评估) → Agent3(方案) → Agent4(发布) → Agent5(复盘)
- 每条Chain独立异常处理，单个Agent失败不影响其他Agent执行

### 步骤4：实现SQLite事件数据库（db/database.py）

- incidents表：事件记录（描述/类型/位置/严重程度/状态/AI分析摘要）
- dispatches表：处置记录（关联事件ID、分析文本、处置方案、发布文案、复盘报告）
- seed_if_empty()预置5个典型交通事件

### 步骤5：构建FastAPI后端 + Vue前端

- 后端API：/api/chat（5Agent分析）、/api/incidents（事件CRUD）、/api/incidents/{id}/dispatches（处置记录）
- 前端：Tab1事件处置（样本选择→输入→5Agent结果分区展示+高德数据面板），Tab2事件档案（列表+详情+处置记录）

## 技术栈

- 多条独立LCEL Chain（每条Agent一条）
- `ChatPromptTemplate` + `StrOutputParser`
- 高德地图REST API（地理编码/周边搜索/路况/路径规划）
- SQLite（事件+处置记录存储）
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下（5个典型交通事件）
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 事件处置界面：5个Agent结果分区展示 + 高德API数据面板（地理编码/周边设施/路况/分流路线）
- 事件档案界面：事件列表、详情、处置记录查看
- 高德在线/离线模式状态指示

## 提示与思考

- 5个Agent是串行还是并行执行？Agent间的数据如何传递？（提示：串行，通过chat()函数依次invoke）
- 高德API数据是在哪个环节注入的？为什么选择这个位置？（提示：在Agent1之后、Agent2之前，因为需要先提取位置信息）
- 如何实现在线/离线双模式切换？对LLM的prompt有什么影响？
- 如果高德API调用失败（网络超时/限流），系统如何降级处理？