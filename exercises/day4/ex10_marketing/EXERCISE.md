## 课题名称

精准营销RFM分析

## 学习目标

- 掌握PydanticOutputParser实现RFM客户分群与营销策略推荐

## 项目概述

精准营销分析助手，基于RFM模型分析客户数据并制定个性化策略。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义Pydantic模型

  - `CustomerProfile`: customer_id, rfm_segment(高价值/成长/流失风险/沉睡), consumption_preference, shopping_habit, marketing_strategy, expected_roi

### 步骤2：使用PydanticOutputParser构建结构化输出Chain

### 步骤3：配置fallback_chain处理解析失败

### 步骤4：System Prompt中注入RFM分析规则和营销策略框架

### 步骤5：构建FastAPI后端 + Vue前端

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

- RFM分群的R/F/M三个维度如何量化打分？
- LLM生成的营销策略如何保证可执行性？
- 预期ROI是LLM估算的还是基于历史数据计算的？