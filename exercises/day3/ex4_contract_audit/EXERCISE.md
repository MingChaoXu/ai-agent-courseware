## 课题名称

合同风险智能审查

## 学习目标

- 掌握PydanticOutputParser实现合同风险审查的结构化输出

## 项目概述

合同风险审查助手，审查6个维度（违约责任/付款条件/知识产权/争议解决/保密条款/终止条款）。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义Pydantic模型

  - `ContractAuditResult`: overall_risk_level(低/中/高), risk_items, missing_clauses, recommendations, summary

### 步骤2：使用PydanticOutputParser构建结构化输出Chain（Prompt + Parser + LLM）

### 步骤3：配置fallback_chain（StrOutputParser）

- 配置fallback_chain（StrOutputParser），解析失败时返回纯文本

### 步骤4：System Prompt中注入6个审查维度的规则

### 步骤5：构建FastAPI后端 + Vue前端（含合同样本选择卡片）

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

- PydanticOutputParser生成的format_instructions具体长什么样？
- 风险等级（低/中/高）是LLM判断的还是规则计算的？各有什么优劣？
- 如何设计HITL（Human-in-the-Loop）流程让法务人员审核AI结果？