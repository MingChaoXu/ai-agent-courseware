# 消费领域AI智能运营平台

## 项目说明

3个AI模块覆盖消费零售全链路：BI分析（ReAct Agent）、智能客服（RAG + Multi-Agent）、精准营销（Structured Output + Monte Carlo）。本文件是代码实现的技术文档，包含架构设计、API说明和代码细节。

## 项目结构

```
ex20_consumer_ai_ops/
├── backend/
│   ├── main.py                     # FastAPI入口，注册路由、初始化数据
│   ├── config.py                   # LLM + Embedding配置
│   ├── data_loader.py              # 数据生成与加载（DataLoader类）
│   ├── agent/agent.py              # Agent初始化包装器
│   ├── api/health.py               # 健康检查 /api/status
│   ├── api/bi.py                   # BI分析接口 /api/bi/*
│   ├── api/cs.py                   # 客服接口 /api/cs/*
│   ├── api/marketing.py            # 营销接口 /api/marketing/*
│   ├── api/data.py                 # 数据接口 /api/data/*
│   ├── models/schemas.py           # Pydantic请求模型
│   ├── services/bi_engine.py       # BI引擎（ReAct Agent + 4工具）
│   ├── services/cs_engine.py       # 客服引擎（FAISS RAG + 4-Agent流水线）
│   ├── services/marketing_engine.py # 营销引擎（RFM + 结构化输出 + 蒙特卡洛）
│   └── data/                       # JSON数据缓存
│       ├── sales.json              # 18个月销售记录
│       ├── customers.json          # 120个客户（含RFM分群）
│       ├── products.json           # 30个商品
│       ├── reviews.json            # 60条评论
│       └── faq.json                # 30条FAQ
├── frontend/
│   └── index.html                  # Vue 3 CDN + ECharts 5 单页应用
├── skill/
│   ├── SKILL.md
│   └── tools/tool.py               # CLI + TeleAgent工具函数
├── data/
│   └── data_schema.md              # 数据Schema说明
├── EXERCISE.md
├── PROJECT_README.md
└── .env.example
```

## 后端架构

### 模块1：BI分析引擎 (services/bi_engine.py)

使用LangGraph `create_react_agent`创建ReAct Agent，配备4个数据工具：

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `_query_sales` | 查询销售数据 | JSON筛选条件 | 匹配的销售记录列表 |
| `_query_customers` | 查询客户数据 | JSON筛选条件 | 匹配的客户列表 |
| `_calc_statistics` | 计算统计指标 | JSON指定维度 | 统计汇总（总额/客单价/同比等） |
| `_generate_chart` | 生成图表配置 | JSON图表类型+数据 | ECharts option JSON |

**执行流程**：
```
用户问题 → create_react_agent(LLM, [4 tools])
  → LLM推理选择工具 → 执行工具 → 观察结果
  → (循环) → 生成最终回答 + 可选图表spec
```

`bi_analyze(question)`返回：`{answer, chart_spec, tool_calls}`

### 模块2：智能客服引擎 (services/cs_engine.py)

RAG知识库 + 4-Agent LCEL流水线：

**RAG知识库**：
- 从FAQ数据构建FAISS向量索引（`_build_vectorstore()`，懒加载）
- 使用`RecursiveCharacterTextSplitter`分割文本
- 检索时返回带相关度评分的文档列表

**4-Agent流水线**：
```
用户问题 → Agent1(意图分类)
  → 输出: intent + confidence
  → Agent2(RAG检索)
  → 输入: question + intent
  → FAISS similarity_search → 检索相关FAQ
  → Agent3(答案生成)
  → 输入: question + retrieved_docs + conversation_history
  → 输出: answer
  → Agent4(情感分析 + 工单创建)
  → 输出: sentiment + ticket(如需)
```

`cs_chat(question, session_id)`返回：`{answer, intent, sentiment, sources, ticket, session_id}`

支持多轮对话：通过`session_id`管理对话历史（内存存储）。

### 模块3：精准营销引擎 (services/marketing_engine.py)

3种LangChain模式 + 蒙特卡洛模拟：

| 功能 | 模式 | Pydantic模型 | LLM |
|------|------|-------------|-----|
| RFM分群 | 纯计算 | - | 否 |
| 客户画像 | PydanticOutputParser | `CustomerPersona` | 是 |
| 情感分析 | PydanticOutputParser | `SentimentReport` | 是 |
| 营销策略 | PydanticOutputParser | `CampaignStrategy` | 是 |
| ROI模拟 | 蒙特卡洛计算 | - | 否 |

**RFM分群**（6个分群）：
- 高价值活跃 / 高价值沉睡 / 中价值成长 / 中价值稳定 / 低价值潜力 / 低价值流失
- 基于Recency（最近消费天数）、Frequency（消费频次）、Monetary（消费金额）三维评分

**蒙特卡洛ROI模拟**：
- 1000次随机模拟
- 输出P10/P50/P90 ROI + 正收益概率
- 按渠道（线上/线下/社交）分别模拟触达→转化→收入

### 数据生成 (data_loader.py)

`DataLoader`类提供懒加载的数据访问：

| 数据 | 数量 | 关键字段 |
|------|------|---------|
| 销售记录 | 18个月 | date, region, category, channel, product_id, amount, orders |
| 客户 | 120个 | customer_id, name, gender, member_level, segment, recency, frequency, monetary, ltv |
| 商品 | 30个 | id, name, category, price, cost |
| 评论 | 60条 | product_id, customer_id, rating, content, sentiment |
| FAQ | 30条 | id, question, answer, category |

随机种子42保证数据可复现。

### API接口

| 方法 | 路径 | 说明 | 需要LLM |
|------|------|------|---------|
| GET | /api/status | 健康检查 | 否 |
| GET | /api/bi/dashboard | BI仪表盘数据 | 否 |
| POST | /api/bi/chat | BI自然语言分析 | 是 |
| GET | /api/bi/sales | 原始销售数据查询 | 否 |
| POST | /api/cs/chat | 客服对话 | 是 |
| GET | /api/cs/faq | FAQ列表 | 否 |
| GET | /api/cs/stats | 客服统计 | 否 |
| GET | /api/cs/history/{session_id} | 对话历史 | 否 |
| GET | /api/marketing/segmentation | RFM分群数据 | 否 |
| POST | /api/marketing/persona | 客户画像生成 | 是 |
| GET | /api/marketing/persona/{customer_id} | 客户画像(GET版) | 是 |
| POST | /api/marketing/sentiment | 情感分析 | 是 |
| POST | /api/marketing/strategy | 营销策略生成 | 是 |
| POST | /api/marketing/simulate | ROI蒙特卡洛模拟 | 否 |
| GET | /api/marketing/visualization | 营销可视化数据 | 否 |
| GET | /api/data/customers | 客户列表 | 否 |
| GET | /api/data/products | 商品列表 | 否 |
| GET | /api/data/reviews | 评论列表 | 否 |

## 前端说明

Vue 3 CDN单页应用，3个Tab页：

**Tab1 - 智能BI**：
- 4个KPI卡片（总销售额/订单量/客单价/同比增长率）
- 4个ECharts图表（月度趋势线图/品类饼图/区域柱状图/交叉热力图）
- 智能数据问答（工具调用展示 + 内联图表渲染）

**Tab2 - 智能客服**：
- 对话面板（意图标签/情感图标/工单卡片/检索来源折叠）
- FAQ分类浏览 + 快速问题按钮
- 服务指标面板（今日咨询/满意度/待处理工单/平均响应）

**Tab3 - 精准营销**：
- 4个KPI卡片（总客户/高价值占比/平均LTV/流失风险）
- RFM散点图 + 分群饼图 + 情感柱状图 + 满意度仪表盘
- 画像生成（选择客户ID → LLM生成画像卡片）
- 策略生成（选择分群+目标 → LLM生成策略卡片）
- ROI模拟器（预算/渠道配比滑块 → 蒙特卡洛直方图 + P10/P50/P90指标）

## Skill说明

封装为11个tool函数：
- `consumer_bi_analyze` / `consumer_bi_dashboard`: BI分析
- `consumer_cs_chat` / `consumer_cs_faq` / `consumer_cs_stats`: 客服
- `consumer_mk_segmentation` / `consumer_mk_persona` / `consumer_mk_sentiment` / `consumer_mk_strategy` / `consumer_mk_simulate`: 营销
- `consumer_health_check`: 健康检查

## 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env填入LLM API配置

# 2. 安装依赖
pip install langchain langchain-openai langgraph faiss-cpu python-dotenv fastapi uvicorn pydantic

# 3. 启动后端
cd backend
python main.py
# 访问 http://localhost:8000
```

## 技术栈

- **LLM框架**: LangChain 1.x + LangGraph (create_react_agent)
- **向量检索**: FAISS (langchain_community.vectorstores)
- **结构化输出**: PydanticOutputParser + Pydantic BaseModel
- **后端**: FastAPI + Uvicorn
- **前端**: Vue 3 (CDN) + ECharts 5
- **LLM接口**: OpenAI兼容协议