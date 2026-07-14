## 课题名称

消费领域AI智能运营平台

## 学习目标

- 掌握ReAct Agent模式（LangGraph `create_react_agent`），实现BI自然语言数据分析与自动图表生成
- 掌握RAG + Multi-Agent架构，实现智能客服（意图分类→知识检索→答案生成→情感分析+工单创建）
- 掌握PydanticOutputParser结构化输出，实现精准营销（客户画像/情感分析/营销策略/ROI蒙特卡洛模拟）

## 项目概述

3个AI模块覆盖消费零售全链路：BI分析（ReAct Agent + 4个数据工具 + ECharts图表生成）、智能客服（FAISS向量检索 + 4-Agent LCEL流水线）、精准营销（RFM分群 + PydanticOutputParser结构化输出 + 蒙特卡洛ROI模拟）。构建FastAPI后端 + Vue 3前端（ECharts 5）的完整全栈项目。

## 任务要求

### 步骤1：实现数据生成与加载（data_loader.py）

  - `DataLoader`类：懒加载，首次访问时生成数据并缓存为JSON
  - 生成数据：18个月销售记录、120个客户（含RFM分群）、30个商品、60条评论、30条FAQ
  - 聚合方法：`dashboard_summary()`（KPI+趋势+品类+区域+热力图）、`segmentation_data()`、`sentiment_data()`、`cs_stats()`

### 步骤2：实现BI分析引擎（services/bi_engine.py）

  - 使用LangGraph `create_react_agent`创建ReAct Agent
  - 定义4个数据工具：
    - `_query_sales(query)`: 按区域/品类/渠道/日期筛选销售数据
    - `_query_customers(query)`: 按分群/会员等级筛选客户数据
    - `_calc_statistics(query)`: 计算统计指标（总额/客单价/同比增长等）
    - `_generate_chart(query)`: 生成ECharts图表配置JSON
  - `bi_analyze(question)`: 调用ReAct Agent执行自然语言分析

### 步骤3：实现智能客服引擎（services/cs_engine.py）

  - RAG知识库：从FAQ数据构建FAISS向量索引（`_build_vectorstore()`）
  - 4-Agent LCEL流水线：
    - Agent1 - 意图分类（query/complaint/faq/refund/delivery/other + 置信度）
    - Agent2 - RAG检索（从FAISS检索相关FAQ，带相关度评分）
    - Agent3 - 答案生成（基于检索结果 + 对话历史）
    - Agent4 - 情感分析 + 工单创建（happy/neutral/angry/sad/anxious + 自动创建工单）
  - `cs_chat(question, session_id)`: 执行完整4-Agent流水线
  - 支持多轮对话（session_id管理对话历史）

### 步骤4：实现精准营销引擎（services/marketing_engine.py）

  - RFM分群（纯计算，无需LLM）：6个分群（高价值活跃/高价值沉睡/中价值成长/中价值稳定/低价值潜力/低价值流失）
  - 客户画像（`generate_persona`）：PydanticOutputParser → `CustomerPersona`（消费偏好/风险因素/推荐动作/LTV/偏好渠道）
  - 情感分析（`analyze_sentiment`）：PydanticOutputParser → `SentimentReport`（品类情感分布/整体满意度）
  - 营销策略（`generate_strategy`）：PydanticOutputParser → `CampaignStrategy`（活动名称/渠道/优惠/预算/ROI/时间线）
  - ROI模拟（`simulate_roi`）：蒙特卡洛模拟1000次，输出P10/P50/P90 ROI和正收益概率

### 步骤5：构建FastAPI后端 + Vue前端

  - 后端API：按模块拆分为5个路由文件（health/bi/cs/marketing/data）
  - 前端：3个Tab页（智能BI仪表盘+对话 / 智能客服对话+FAQ / 精准营销分群+画像+策略+ROI模拟器）
  - 前端使用ECharts 5渲染图表（趋势线/饼图/柱状图/热力图/散点图/仪表盘/直方图）

## 技术栈

- **BI模块**: LangGraph `create_react_agent` + 4个Tool
- **客服模块**: FAISS向量检索 + 4条LCEL Chain（Multi-Agent）
- **营销模块**: `PydanticOutputParser`结构化输出 + 蒙特卡洛模拟
- **后端**: FastAPI + Uvicorn
- **前端**: Vue 3 (CDN) + ECharts 5
- **LLM接口**: OpenAI兼容协议

## 输入数据

- 数据由`data_loader.py`程序化生成（随机种子42保证可复现）
- 数据Schema详见 `data/data_schema.md`
- 生成后缓存为JSON文件在 `backend/data/` 目录下

## 预期输出

- BI界面：4个KPI卡片 + 4个图表（趋势/品类/区域/热力图） + 智能数据问答（含工具调用展示和内联图表）
- 客服界面：对话面板（意图标签/情感图标/工单卡片/检索来源） + FAQ分类浏览 + 服务指标
- 营销界面：RFM散点图 + 分群饼图 + 情感柱状图 + 满意度仪表盘 + 画像生成 + 策略生成 + ROI模拟器（含蒙特卡洛直方图）

## 提示与思考

- ReAct Agent与传统Chain有什么区别？它如何决定调用哪个工具？（提示：ReAct = Reason + Act，LLM自主推理选择工具）
- RAG检索为什么用FAISS而不是直接全文搜索？（提示：语义相似度匹配，不依赖关键词完全匹配）
- PydanticOutputParser如何保证LLM输出的结构化数据格式正确？（提示：通过format_instructions注入格式说明 + Pydantic模型校验）
- 蒙特卡洛模拟的P10/P50/P90分别代表什么？为什么用百分位数而不是平均值？（提示：P50是中位数，P10-P90展示不确定性范围）