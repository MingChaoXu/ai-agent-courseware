## 课题名称

社会治理综合智能体

## 学习目标

- 掌握多Agent并行+条件分支架构，实现社会治理事件处理

## 项目概述

4个Agent协作：event_entry_agent(事件录入) + legal_consultation_agent(法律咨询,条件触发) + brief_generation_agent(通报生成) + alert_agent(预警处置)。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义各Agent的LCEL Chain

  - `event_entry_agent`: 录入社会治理事件，分类归档
  - `legal_consultation_agent`: 为纠纷类事件提供法律咨询建议（条件触发：仅纠纷类）
  - `brief_generation_agent`: 生成社会治理通报
  - `alert_agent`: 评估事件风险等级，触发预警

### 步骤2：create_agent()返回包含4条Chain的字典

### 步骤3：chat()函数调用各Chain

- chat()函数调用各Chain，legal_consultation_agent仅在纠纷类事件时触发

### 步骤4：构建FastAPI后端 + Vue前端

- 构建FastAPI后端 + Vue前端，展示多Agent并行+条件分支

## 技术栈

- 多条独立LCEL Chain（每条Agent一条）
- `ChatPromptTemplate` + `StrOutputParser`
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 对话式交互界面，用户输入文本后返回AI分析结果
- 多Agent协作结果，按模块分区展示

## 提示与思考

- 条件分支如何实现？如何根据事件类型决定是否触发legal_consultation_agent？
- 并行执行和串行执行在什么场景下各有什么优势？
- 风险等级评估如何量化？alert_agent的判定标准如何设计？