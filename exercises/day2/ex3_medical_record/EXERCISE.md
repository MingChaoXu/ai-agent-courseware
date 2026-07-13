## 课题名称

基层门诊AI辅助诊疗

## 学习目标

- 掌握PydanticOutputParser结构化输出，设计多模块Agent系统+SQLite患者数据库

## 项目概述

5模块医疗AI助手（病历生成/检验解读/诊疗推荐/病历质控/时序分析）。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义Pydantic模型

  - `MedicalRecord`: patient_info, chief_complaint, present_illness, past_history, physical_examination, preliminary_diagnosis, treatment_plan
  - `LabReportInterpretation`: report_type, key_indicators(含is_abnormal布尔标注), overall_interpretation, clinical_correlation, follow_up_suggestions
  - `TreatmentPlan`: possible_diagnoses, recommended_exams, medication_suggestions, precautions, risk_alerts
  - `QualityControlResult`: quality_level(甲/乙/丙), missing_items, nonstandard_terms, logic_issues, modification_suggestions, overall_score
  - `TimelineAnalysis`: patient_summary, disease_progression, key_changes, treatment_effectiveness, risk_assessment, future_recommendations, follow_up_plan

### 步骤2：构建5条独立LCEL Chain（Prompt + Parser + LLM）

- 构建5条独立LCEL Chain（Prompt + Parser + LLM），每条Chain配置fallback

### 步骤3：实现SQLite数据库层（patients + visits两张表）

- 实现SQLite数据库层（patients + visits两张表），包含CRUD和种子数据

### 步骤4：统一/api/chat接口通过module参数选择模块

- 统一/api/chat接口通过module参数选择模块，patient_id可选归档

### 步骤5：实现/api/patients路由（CRUD + 就诊记录 + timeline-analysis端点）

### 步骤6：构建前端5模块Tab界面（含患者档案管理、就诊时间轴、AI时序分析）

## 技术栈

- `PydanticOutputParser`（结构化输出解析）
- `ChatPromptTemplate`（提示模板）
- LCEL（管道式Chain组装）
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 对话式交互界面，用户输入文本后返回AI分析结果
- 结构化JSON输出，前端渲染为卡片式展示

## 提示与思考

- PydanticOutputParser是如何让LLM输出指定格式的？提示词中做了什么？
- 如果LLM输出的JSON不合法，Parser会怎样？fallback机制如何工作？
- SQLite作为嵌入式数据库，与Redis/PostgreSQL在医疗场景中各有什么适用边界？