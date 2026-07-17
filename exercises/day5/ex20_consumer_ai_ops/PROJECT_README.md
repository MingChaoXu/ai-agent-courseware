# 消费领域AI智能运营平台

## 项目说明

3个AI模块覆盖消费零售全链路：BI分析（ReAct Agent + 14工具 + 多轮对话 + 6个预计算面板）、智能客服（RAG + 5-Agent流水线 + 满意度评分）、精准营销（Structured Output + Monte Carlo 1000次 + 流失预测 + A/B测试）。本文件是代码实现的技术文档，包含架构设计、API说明和代码细节。

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
│   ├── services/bi_engine.py       # BI引擎（ReAct Agent + 14工具 + 6预计算 + 多轮对话）
│   ├── services/cs_engine.py       # 客服引擎（FAISS RAG + 5-Agent流水线 + 满意度）
│   ├── services/marketing_engine.py # 营销引擎（RFM + 结构化输出 + 蒙特卡洛 + 流失预测 + A/B测试）
│   └── data/                       # JSON数据缓存
│       ├── sales.json              # 18个月销售记录
│       ├── customers.json          # 120个客户（含RFM分群）
│       ├── products.json           # 30个商品
│       ├── reviews.json            # 60条评论
│       └── faq.json                # 30条FAQ
├── frontend/
│   └── index.html                  # Vue 3 CDN + ECharts 5 单页应用（暗色主题）
├── skill/
│   ├── SKILL.md
│   └── tools/tool.py               # CLI + TeleAgent工具函数（21个tool）
├── data/
│   └── data_schema.md              # 数据Schema说明
├── requirements.txt                # Python依赖
├── EXERCISE.md
├── PROJECT_README.md
└── .env.example
```

## 后端架构

### 模块1：BI分析引擎 (services/bi_engine.py)

使用LangGraph `create_react_agent`创建ReAct Agent，配备14个数据工具，支持多轮对话：

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `_query_sales` | 查询销售数据 | JSON筛选条件 | 匹配的销售记录列表 |
| `_query_customers` | 查询客户数据 | JSON筛选条件 | 匹配的客户列表 |
| `_calc_statistics` | 计算统计指标 | JSON指定维度 | 统计汇总（总额/中位数/标准差/百分位等） |
| `_predict_trend` | 趋势预测 | JSON指定指标+预测月数 | 历史数据+预测值+趋势方向+R²置信度 |
| `_detect_anomaly` | 异常检测 | JSON指定指标+Z-score阈值 | 异常值列表+Z分数 |
| `_generate_chart` | 生成图表配置 | JSON图表类型+数据 | ECharts option JSON（含radar/funnel类型） |
| `_compare_periods` | 同比环比分析 | JSON指标+基准期+对比期+分组维度 | 各分组同比/环比增长率 |
| `_root_cause_analysis` | 归因分析 | JSON指标+时间范围 | 维度拆解（区域/品类/渠道贡献度） |
| `_cohort_analysis` | 同期群分析 | JSON分群维度+期数 | 各群留存率+流失率 |
| `_funnel_analysis` | 转化漏斗 | JSON漏斗阶段+时间范围 | 各环节转化率+流失率 |
| `_correlation_analysis` | 相关性分析 | JSON两组变量 | Pearson相关系数+p值 |
| `_kpi_health_check` | KPI健康度 | JSON时间范围 | 五维评分+综合健康分 |
| `_product_analysis` | 商品组合分析 | JSON时间范围 | BCG矩阵+品类集中度+明星/现金牛/问题/瘦狗分类 |
| `_auto_insight` | 自动洞察 | JSON时间范围 | 自动扫描异常+机会+趋势变化 |

**执行流程**：
```
用户问题 → create_react_agent(LLM, [14 tools])
  → LLM推理选择工具 → 执行工具 → 观察结果
  → (循环) → 生成最终回答 + 可选图表spec
```

**多轮对话**：通过`session_id`管理对话历史（内存存储，最近20条消息），前5轮对话注入Agent上下文。

**预计算报告函数**（6个，无需LLM，直接返回结构化数据）：

| 函数 | 对应API | 说明 |
|------|---------|------|
| `get_compare_report()` | `GET /api/bi/compare` | 同比环比（支持group_by维度） |
| `get_root_cause_report()` | `GET /api/bi/root-cause` | 归因分析（区域/品类/渠道拆解） |
| `get_funnel_report()` | `GET /api/bi/funnel` | 转化漏斗 |
| `get_cohort_report()` | `GET /api/bi/cohort` | 同期群留存 |
| `get_kpi_health_report()` | `GET /api/bi/kpi-health` | KPI健康度雷达 |
| `get_auto_insight_report()` | `GET /api/bi/auto-insight` | 自动洞察扫描 |

`bi_analyze(question, session_id)`返回：`{answer, chart_spec, tool_calls, session_id}`

### 模块2：智能客服引擎 (services/cs_engine.py)

RAG知识库 + 5-Agent LCEL流水线：

**RAG知识库**：
- 从FAQ数据构建FAISS向量索引（`_build_vectorstore()`，懒加载）
- 使用`RecursiveCharacterTextSplitter`分割文本
- 检索时返回带相关度评分的文档列表

**5-Agent流水线**：
```
用户问题 → Agent1(意图分类 + 子类型)
  → 输出: intent + confidence + sub_type + keywords
  → Agent2(RAG检索)
  → 输入: question + intent
  → FAISS similarity_search → 检索相关FAQ
  → Agent3(答案生成，含对话历史)
  → 输入: question + retrieved_docs + conversation_history
  → 输出: answer
  → Agent4(情感分析 + 工单创建)
  → 输出: sentiment + ticket(如需) + emotion_intensity
  → Agent5(满意度评分)
  → 输出: score + aspects(响应速度/准确性/态度) + improvement
```

`cs_chat(question, session_id)`返回：`{answer, intent, sentiment, sources, ticket, satisfaction, session_id}`

### 模块3：精准营销引擎 (services/marketing_engine.py)

3种LangChain模式 + 蒙特卡洛模拟 + 流失预测 + A/B测试：

| 功能 | 模式 | Pydantic模型 | LLM |
|------|------|-------------|-----|
| RFM分群 | 纯计算 | - | 否 |
| 客户画像（含流失概率） | PydanticOutputParser | `CustomerPersona` | 是 |
| 情感分析 | PydanticOutputParser | `SentimentReport` | 是 |
| 营销策略（含KPI） | PydanticOutputParser | `CampaignStrategy` | 是 |
| ROI模拟 | 蒙特卡洛1000次 | - | 否 |
| 流失预测 | RFM加权评分 | - | 否 |
| A/B测试 | 统计模拟 | - | 否 |

**RFM分群**（6个分群）：
- 高价值活跃 / 高价值沉睡 / 中价值成长 / 中价值稳定 / 低价值潜力 / 低价值流失
- 基于Recency（最近消费天数）、Frequency（消费频次）、Monetary（消费金额）三维评分

**蒙特卡洛ROI模拟**：
- 1000次随机模拟
- 输出P10/P50/P90 ROI + 正收益概率
- 按渠道（线上直营/线上分销/线下门店）分别模拟触达→转化→收入
- 渠道配比支持中英文键名映射

**流失预测**：
- 基于RFM加权评分模型（Recency 0.4 / Frequency 0.35 / Monetary 0.25）
- 非活跃客户+0.15惩罚
- 输出高/中/低风险客户数、TOP10风险客户、挽留建议

**A/B测试模拟**：
- 计算最小样本量和统计功效
- Monte Carlo模拟实验结果
- Chi-squared/Z检验输出p-value和显著性判断
- 支持分群维度分析

### 数据生成 (data_loader.py)

`DataLoader`类提供懒加载的数据访问：

| 数据 | 数量 | 关键字段 |
|------|------|---------|
| 销售记录 | ~2160条 | date, region, category, channel, sales_amount, order_count, customer_count, avg_order_value, return_rate |
| 客户 | 120个 | id, name, gender, age, region, city, member_level, segment, recency_days, frequency, monetary, r/f/m_score, ltv, is_active, churn_risk |
| 商品 | 30个 | id, name, category, price, cost |
| 评论 | 60条 | product_id, product_name, category, rating, content, sentiment, date |
| FAQ | 30条 | id, question, answer, category |

随机种子42保证数据可复现。

### API接口

| 方法 | 路径 | 说明 | 需要LLM |
|------|------|------|---------|
| GET | /api/status | 健康检查 | 否 |
| GET | /api/bi/dashboard | BI仪表盘数据 | 否 |
| POST | /api/bi/chat | BI自然语言分析（多轮对话） | 是 |
| GET | /api/bi/history/{session_id} | BI对话历史 | 否 |
| GET | /api/bi/sales | 原始销售数据查询（分页） | 否 |
| GET | /api/bi/compare | 同比环比分析（?group_by=region） | 否 |
| GET | /api/bi/root-cause | 归因分析（维度拆解） | 否 |
| GET | /api/bi/funnel | 转化漏斗 | 否 |
| GET | /api/bi/cohort | 同期群分析 | 否 |
| GET | /api/bi/kpi-health | KPI健康度评分 | 否 |
| GET | /api/bi/auto-insight | 自动洞察扫描 | 否 |
| POST | /api/agent/query | Agent统一调度（意图分类+模块路由） | 是 |
| GET | /api/agent/modules | 可用模块列表 | 否 |
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
| GET | /api/marketing/churn | 流失风险预测 | 否 |
| POST | /api/marketing/ab-test | A/B测试模拟 | 否 |
| GET | /api/data/customers | 客户列表 | 否 |
| GET | /api/data/products | 商品列表 | 否 |
| GET | /api/data/reviews | 评论列表 | 否 |

## 前端说明

Vue 3 CDN单页应用，3个Tab页，支持暗色主题切换：

**Tab1 - 智能BI**：
- 4个KPI卡片（总销售额/订单量/客单价/环比增长率）
- 4个ECharts图表（月度趋势线图/品类饼图/区域柱状图/交叉热力图）
- 5个预计算分析面板：同比环比（分组柱图）/ KPI健康度（雷达图+综合分）/ 转化漏斗（ECharts funnel）/ 同期群（留存曲线+指标表）/ 自动洞察（异常/机会卡片+严重度标签）
- 智能数据问答（支持多轮对话 + 工具调用展示 + 内联图表渲染）
- 快捷问题：趋势预测、异常检测、归因分析、自动洞察、品类BCG

**Tab2 - 智能客服**：
- 对话面板（意图标签/情感图标/工单卡片/满意度星级/检索来源折叠）
- FAQ分类浏览 + 快速问题按钮
- 服务指标面板（今日咨询/满意度/待处理工单/平均响应）

**Tab3 - 精准营销**：
- 4个KPI卡片（总客户/高价值占比/平均LTV/流失风险）
- RFM散点图 + 分群饼图 + 情感柱状图 + 满意度仪表盘
- 流失风险预测区（高/中/低风险数 + TOP10风险客户 + 挽留建议）
- 画像生成（选择客户 → LLM生成画像卡片含流失概率）
- 策略生成（选择分群+目标 → LLM生成策略卡片含KPI指标）
- ROI模拟器（预算/渠道配比滑块 → 蒙特卡洛直方图 + P10/P50/P90指标 + 智能推荐）
- A/B测试模拟器（对照组转化率/预期提升/样本量/置信水平 → 统计显著性 + 推荐）

## Skill说明

封装为21个tool函数：
- `consumer_bi_analyze` / `consumer_bi_dashboard`: BI分析（14工具+多轮）
- `consumer_bi_compare` / `consumer_bi_root_cause` / `consumer_bi_funnel` / `consumer_bi_cohort` / `consumer_bi_correlation` / `consumer_bi_kpi_health` / `consumer_bi_product` / `consumer_bi_insight`: BI预计算报告
- `consumer_cs_chat` / `consumer_cs_faq` / `consumer_cs_stats`: 客服（5-Agent+满意度）
- `consumer_mk_segmentation` / `consumer_mk_persona` / `consumer_mk_sentiment` / `consumer_mk_strategy` / `consumer_mk_simulate` / `consumer_mk_churn` / `consumer_mk_ab_test`: 营销
- `consumer_health_check`: 健康检查

## 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env填入LLM API配置

# 2. 安装依赖
pip install -r requirements.txt

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
- **前端**: Vue 3 (CDN) + ECharts 5 + 暗色主题
- **LLM接口**: OpenAI兼容协议