## 课题名称

MCP工具协议演示Agent

## 学习目标

- 理解MCP（Model Context Protocol）三类工具（感知/执行/协作），掌握Agent工具调用机制

## 项目概述

MCP协议演示助手，使用感知类、执行类和协作类工具。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义工具函数

  - `web_search`: 搜索网络信息（感知类工具），输入关键词返回搜索结果
  - `code_execute`: 执行代码（执行类工具），输入Python代码返回结果
  - `send_notification`: 发送通知（协作类工具），输入内容返回发送状态

### 步骤2：使用langgraph.prebuilt.create_react_agent创建Agent

### 步骤3：在工具description中标注MCP工具类型（感知/执行/协作）

### 步骤4：实现chat()函数通过agent.invoke()获取回答

### 步骤5：构建FastAPI后端 + Vue前端

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

- MCP协议的三类工具（感知/执行/协作）分别对应什么场景？
- Agent如何根据用户意图选择合适的工具类型？
- 如何将LangChain Tool映射为MCP协议格式？