## 课题名称

ReAct推理原理实验

## 学习目标

- 理解ReAct（Reasoning + Acting）推理范式，掌握LangGraph create_react_agent实现工具调用循环

## 项目概述

政务咨询助手，使用Thought → Action → Observation循环推理。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义工具函数

  - `search_policy`: 搜索政务政策信息，输入关键词返回政策内容
  - `calculate`: 计算数学表达式，输入表达式字符串返回结果

### 步骤2：使用langgraph.prebuilt.create_react_agent创建Agent

- 使用langgraph.prebuilt.create_react_agent创建Agent，传入LLM和工具列表

### 步骤3：在Agent的prompt中指定ReAct推理流程（Thought → Action → Observation）

### 步骤4：实现chat()函数

- 实现chat()函数，通过agent.invoke()传入messages获取最终回答

### 步骤5：构建FastAPI后端 + Vue前端

- 构建FastAPI后端 + Vue前端，实现交互式对话界面

## 技术栈

- LangGraph `create_react_agent`
- `langchain_core.tools.Tool`（工具定义）
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 对话式交互界面，用户输入文本后返回AI分析结果
- 工具调用过程可视化，展示Thought → Action → Observation

## 提示与思考

- ReAct循环中，LLM是如何决定调用哪个工具的？
- 如果工具返回错误信息，Agent会如何处理？
- 对比直接调用LLM，ReAct模式在什么场景下更有优势？