## 课题名称

多模态处理三种模式对比

## 学习目标

- 理解多模态信息处理的三种模式（NATIVE/EXTRACT/TOOL）及其优劣

## 项目概述

多模态AI技术教学助手，帮助理解多模态信息处理的不同方式。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义对比数据

  - `NATIVE模式`: 直接多模态输入到GPT-4o（优势: 端到端,信息损失小, 劣势: 成本高,延迟大）
  - `EXTRACT模式`: OCR/检测转文本后再给LLM（优势: 成本低,可复用, 劣势: 信息有损失）
  - `TOOL模式`: Agent调用专业视觉工具（优势: 灵活可控,可扩展, 劣势: 架构复杂）

### 步骤2：使用ChatPromptTemplate + StrOutputParser构建教学对话Chain

### 步骤3：chat()函数将对比数据注入context

- chat()函数将对比数据注入context，让LLM基于参考信息回答

### 步骤4：构建FastAPI后端 + Vue前端

## 技术栈

- `ChatPromptTemplate` + `StrOutputParser`
- LCEL Chain
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 对话式交互界面，用户输入文本后返回AI分析结果
- LLM生成的文本回答

## 提示与思考

- NATIVE模式为什么成本高？Token计算方式和纯文本有什么不同？
- EXTRACT模式的信息损失具体体现在哪些方面？
- TOOL模式如何与ReAct Agent结合？工具的description如何影响Agent选择？