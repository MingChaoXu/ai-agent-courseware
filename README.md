---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'be141b36-f943-40cf-99fd-8c2380032058'
  PropagateID: 'be141b36-f943-40cf-99fd-8c2380032058'
  ReservedCode1: '8a411a82-b1eb-4530-b6cb-23a2f5986a24'
  ReservedCode2: '8a411a82-b1eb-4530-b6cb-23a2f5986a24'
---

# 区县AI赋能培训课程

面向电信行业客户经理与解决方案经理的5天AI智能体实战培训课程，涵盖AI理论与实践、RAG知识库、文档审核、多模态数据分析、复杂智能体等16+行业场景。

## 课程结构

| 天数 | 主题 | 形式 |
|------|------|------|
| Day 1 | AI理论与实践基础 | 理论授课 |
| Day 2 | TeleAgent实战与RAG原理 | 实战演练 |
| Day 3 | 上下文工程与文档审核 | 实战演练 |
| Day 4 | 多模态工具生态与数据分析 | 实战演练 |
| Day 5 | 复杂智能体评估与路演 | 实战演练 |

## 目录说明

```
├── Day1_AI理论与实践基础.html
├── Day2_TeleAgent实战与RAG原理.html
├── Day3_上下文工程与文档审核.html
├── Day4_多模态工具生态与数据分析.html
├── Day5_复杂智能体评估与路演.html
├── requirements.txt
├── .env.example
└── exercises/
    ├── common/
    │   ├── shared_utils.py
    │   ├── teleagent_client.py
    │   ├── training_utils.py
    │   └── gen_sample_data.py
    ├── data/
    │   ├── gov_faq.json
    │   ├── industrial_kb.json
    │   ├── contract_samples.json
    │   └── production_data.json
    ├── day2/
    ├── day3/
    ├── day4/
    └── day5/
```

## 实战课题一览

### Day 2 — TeleAgent实战与RAG原理

| 编号 | 课题 | 目录 |
|------|------|------|
| ex0 | ReAct推理原理 | ex0_react_principle/ |
| ex1 | 政务智能问答 | ex1_gov_qa/ |
| ex2 | 工业知识库检索 | ex2_industrial_kb/ |
| ex3 | 基层门诊AI辅助诊疗 | ex3_medical_record/ |
| ex3.5 | 上下文压缩 | ex3_5_context_compress/ |

### Day 3 — 上下文工程与文档审核

| 编号 | 课题 | 目录 |
|------|------|------|
| ex3.8 | 用户记忆管理 | ex3_8_user_memory/ |
| ex4 | 合同风险审核 | ex4_contract_audit/ |
| ex5 | 招标文件分析 | ex5_bidding/ |
| ex6 | 工程建设文档 | ex6_construction_doc/ |
| ex7 | HR简历筛选 | ex7_hr_review/ |
| ex8 | 治理简报生成 | ex8_governance_brief/ |

### Day 4 — 多模态工具生态与数据分析

| 编号 | 课题 | 目录 |
|------|------|------|
| ex8.5 | 多模态理解 | ex8_5_multimodal/ |
| ex9 | 制造业BI分析 | ex9_manufacturing_bi/ |
| ex10 | 营销策略生成 | ex10_marketing/ |
| ex11 | 舆情情感分析 | ex11_sentiment/ |
| ex12 | 质量检测报告 | ex12_quality_inspect/ |
| ex13 | CV安全巡检 | ex13_cv_safety/ |
| ex13.5 | MCP协议实践 | ex13_5_mcp_protocol/ |

### Day 5 — 复杂智能体评估与路演

| 编号 | 课题 | 目录 |
|------|------|------|
| ex14 | 政务服务智能体 | ex14_gov_service/ |
| ex15 | 治理多智能体 | ex15_governance_agent/ |
| ex15.5 | 事件驱动架构 | ex15_5_event_driven/ |
| ex16 | 消融评估框架 | ex16_ablation_eval/ |
| ex17 | 综合路演 | ex17_roadshow/ |

## 快速开始

### 1. 安装依赖

```bash
pip install langchain>=1.0.0 langchain-core>=1.0.0 langchain-openai>=1.0.0 \\
    langchain-community>=0.3.0 langchain-text-splitters>=1.0.0 \\
    langchain-classic>=0.1.0 langgraph>=0.1.0 \\
    faiss-cpu>=1.7.4 openai>=1.0.0 python-dotenv>=1.0.0
```

### 2. 配置API

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key 和模型配置
```

`.env` 配置说明：

| 变量 | 说明 |
|------|------|
| OPENAI_API_KEY | LLM API 密钥 |
| OPENAI_API_BASE | LLM API 基础地址 |
| OPENAI_MODEL_NAME | LLM 模型名称 |
| EMBEDDING_MODEL_NAME | Embedding 模型名称 |
| EMBEDDING_API_KEY | Embedding API 密钥 |
| EMBEDDING_API_BASE | Embedding API 地址 |

### 3. 生成样例数据

```bash
cd exercises/common
python gen_sample_data.py
```

### 4. 运行课题

每个课题目录下都有独立的 `run.py`，可直接运行：

```bash
cd exercises/day2/ex1_gov_qa
python run.py
```

## 技术栈

- **LLM 框架**: LangChain 1.x + LangGraph
- **向量存储**: FAISS (本地内存)
- **Embedding**: BAAI/bge-m3 (1024维)
- **LLM 接口**: OpenAI 兼容协议

## 许可

本课程材料仅供培训教学使用。