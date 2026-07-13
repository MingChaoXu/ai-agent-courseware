## 课题名称

施工文档智能生成

## 学习目标

- 掌握ChatPromptTemplate动态切换System Prompt，实现多文档类型生成

## 项目概述

施工文档生成助手，支持工程概况/施工方案/安全措施/质量控制等章节。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：构建LLM Chain

- 使用ChatPromptTemplate定义提示模板

### 步骤2：在System Prompt中定义文档规范格式和专业术语要求

### 步骤3：实现chat()函数处理用户输入并返回生成的文档

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

- 如何根据不同文档类型（施工方案/安全方案/质检报告）动态切换System Prompt？
- 生成的文档如何保证格式规范性？是否需要后处理？
- StrOutputParser vs PydanticOutputParser在什么场景下各有什么优势？