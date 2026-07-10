## 课题名称

ReAct推理原理

## 学习目标

- 理解Agent核心框架（LLM + Context + Tools）
- 掌握ReAct循环（Thought → Action → Observation）
- 理解上下文对推理的影响

## 任务要求

### 步骤1：理解Agent核心三要素框架

- 了解LLM、Context、Tools三个核心组件的作用
- 手动组装一个简单Agent，将三要素组合到一起运行

### 步骤2：手动模拟ReAct循环

- 用代码跑通 Thought → Action → Observation 循环
- 打印每一步的中间状态，直观理解推理过程

### 步骤3：上下文消融实验

- 逐步移除上下文信息（从完整上下文 → 部分上下文 → 无上下文）
- 观察并记录每一步推理质量的变化

### 步骤4：用LangChain原生API构建真实的ReAct Agent

- 使用 `langgraph.create_react_agent` 构建真实Agent
- 定义Tool并注册到Agent中，观察完整的ReAct推理流程

## 技术栈

- LangChain 1.x
- LangGraph (`create_react_agent`, `Tool`)

## 输入数据

- 模拟的数学计算工具（加、减、乘、除）
- 模拟的天气查询工具（根据城市返回天气信息）

## 预期输出

- ReAct循环完整日志（包含每一步的Thought、Action、Observation）
- 上下文消融对比结果（完整/部分/无上下文下推理质量差异）
- 真实Agent运行截图或日志

## 提示与思考

- ReAct的核心思想是什么？为什么不直接让LLM回答，而要先行动再观察？
- 上下文消融实验中，哪个上下文信息对推理影响最大？
- `create_react_agent` 中的Tool是如何被LLM感知到的？提示词里发生了什么？