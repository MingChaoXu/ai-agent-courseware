## 课题名称

制造业BI分析Agent

## 学习目标

- 掌握LangGraph create_react_agent实现制造业BI分析，对比Agent与Chain模式

## 项目概述

制造业BI分析助手，使用数据查询和代码执行工具分析生产数据。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义工具函数

  - `query_production_data`: 查询生产数据，输入查询条件返回产线产量、良品率等
  - `execute_code`: 执行Python代码进行数据分析，输入代码字符串返回结果

### 步骤2：使用langgraph.prebuilt.create_react_agent创建Agent

### 步骤3：实现chat()函数通过agent.invoke()获取回答

### 步骤4：对比ReAct Agent与普通LCEL Chain在数据分析场景下的差异

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

- execute_code工具的安全沙箱如何设计？如何防止恶意代码？
- Agent模式vs直接写SQL查询，在什么场景下各有什么优势？
- 如何扩展更多工具（如生成图表、发送报告）？