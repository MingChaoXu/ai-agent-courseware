## 课题名称

金融舆情智能分析

## 学习目标

- 掌握PydanticOutputParser实现金融舆情的情感分析与风险评估

## 项目概述

金融舆情分析助手，逐条分析情感并评估风险等级（红/黄/绿）。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义Pydantic模型

  - `SentimentReport`: overall_sentiment(正面/负面/中性), red_count, yellow_count, green_count, hot_topics, items(逐条分析), summary

### 步骤2：使用PydanticOutputParser构建结构化输出Chain

### 步骤3：配置fallback_chain处理解析失败

### 步骤4：System Prompt中注入舆情分析和风险等级评估规则

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

- 批量分析多条舆情时，如何控制LLM的Token消耗？
- 风险等级（红/黄/绿）的判定标准如何设计？
- 热点话题的识别基于什么算法？LLM如何提取关键话题？