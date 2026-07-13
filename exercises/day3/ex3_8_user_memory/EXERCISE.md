## 课题名称

用户记忆管理Agent

## 学习目标

- 掌握多Agent协作架构，理解短期/长期/工作记忆的区分与管理

## 项目概述

3个Agent协作：memory_agent(档案管理) + qa_agent(问答) + update_agent(信息更新)。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义各Agent的LCEL Chain

  - `memory_agent`: 管理用户档案信息，包括基本信息、偏好和历史记录
  - `qa_agent`: 基于用户记忆和历史记录回答问题
  - `update_agent`: 解析用户输入，更新用户档案

### 步骤2：create_agent()返回包含3条Chain的字典

### 步骤3：chat()函数并行调用3条Chain

- chat()函数并行调用3条Chain，将结果拼接为结构化输出

### 步骤4：构建FastAPI后端 + Vue前端

- 构建FastAPI后端 + Vue前端，展示多Agent协作结果

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

- 三个Agent并行执行vs串行执行，各有什么优缺点？
- 如何实现Agent之间的信息传递（如qa_agent读取memory_agent的结果）？
- 用户记忆的持久化应该用文件还是数据库？各有什么考虑？