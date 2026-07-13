# 基层门诊AI辅助诊疗

## 项目说明

5模块医疗AI助手（病历生成/检验解读/诊疗推荐/病历质控/时序分析）。本文件是代码实现的技术文档，包含架构设计、API说明和代码细节。

## 项目结构

```
ex3_medical_record/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── agent/agent.py
│   ├── api/chat.py
│   ├── api/health.py
│   ├── models/schemas.py
│   ├── api/patients.py
│   ├── db/database.py
│   └── db/__init__.py
├── frontend/
│   └── index.html          # Vue 3 CDN 单页应用
├── skill/
│   ├── SKILL.md             # Skill文档
│   └── tools/
│       └── tool.py          # TeleAgent Skill工具
├── data/                    # 测试数据
├── EXERCISE.md              # 学生任务要求
├── PROJECT_README.md        # 本文件
└── .env.example             # 环境变量模板
```

## 后端架构

### 结构化输出架构

使用`PydanticOutputParser`实现LLM输出的结构化控制：

**Pydantic模型定义**：
- `MedicalRecord`: patient_info, chief_complaint, present_illness, past_history, physical_examination, preliminary_diagnosis, treatment_plan
- `LabReportInterpretation`: report_type, key_indicators(含is_abnormal布尔标注), overall_interpretation, clinical_correlation, follow_up_suggestions
- `TreatmentPlan`: possible_diagnoses, recommended_exams, medication_suggestions, precautions, risk_alerts
- `QualityControlResult`: quality_level(甲/乙/丙), missing_items, nonstandard_terms, logic_issues, modification_suggestions, overall_score
- `TimelineAnalysis`: patient_summary, disease_progression, key_changes, treatment_effectiveness, risk_assessment, future_recommendations, follow_up_plan

**Chain组装**：`ChatPromptTemplate + format_instructions → LLM → PydanticOutputParser`

**Fallback机制**：主Chain解析失败时，自动切换到`StrOutputParser`返回纯文本，保证服务可用性。

`analyze()`函数调用`agent["chain"].invoke()`，成功返回`result.model_dump()`，失败则走fallback。

### API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查（返回5个模块列表） |
| POST | /api/chat | 结构化分析（module参数选择模块，patient_id可选归档） |
| GET | /api/patients | 患者列表（支持关键词搜索） |
| POST | /api/patients | 创建患者 |
| GET | /api/patients/{id} | 患者详情 |
| PUT | /api/patients/{id} | 更新患者信息 |
| DELETE | /api/patients/{id} | 删除患者 |
| GET | /api/patients/{id}/visits | 就诊记录列表 |
| POST | /api/patients/visits | 新增就诊记录 |
| DELETE | /api/patients/visits/{id} | 删除就诊记录 |
| POST | /api/patients/timeline-analysis | AI时序病情分析 |

### 关键文件说明

- `agent/agent.py`: 核心Agent/Chain逻辑，定义Pydantic模型、工具函数、Chain工厂
- `api/chat.py`: 对话接口，调用agent并返回结果
- `api/health.py`: 健康检查接口
- `models/schemas.py`: Pydantic请求/响应模型（ChatRequest/ChatResponse/HealthResponse）
- `config.py`: 从.env读取LLM配置（API Key/Model/Base URL）
- `main.py`: FastAPI入口，注册路由、初始化Agent、CORS配置

## 前端说明

Vue 3 CDN单页应用，无需构建工具。主要功能：
- 对话式交互界面
- 结构化结果卡片展示（中文标签映射）
- 样本快速选择（嵌入测试数据）
- 健康状态实时显示

## Skill说明

封装为6个tool函数（5个AI模块 + health_check），支持CLI指定模块和输入文本。

## 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env填入LLM API配置

# 2. 安装依赖
pip install langchain langchain-openai langgraph faiss-cpu python-dotenv fastapi uvicorn

# 3. 启动后端
cd backend
python main.py
# 访问 http://localhost:8000
```

## 技术栈

- **LLM框架**: LangChain 1.x + LangGraph
- **后端**: FastAPI + Uvicorn
- **前端**: Vue 3 (CDN)
- **LLM接口**: OpenAI兼容协议