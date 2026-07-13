## 课题名称

电力安全CV检测Agent

## 学习目标

- 掌握LangGraph create_react_agent实现电力作业现场安全检测

## 项目概述

电力行业安全检测助手，使用PPE检测、安全距离检测和环境检测工具。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义工具函数

  - `ppe_check`: 检测人员PPE佩戴情况（安全帽/手套/鞋/服），输入场景描述返回检测结果
  - `distance_check`: 检查人员与带电设备的安全距离，输入场景描述返回距离检测结果
  - `environment_check`: 检查作业环境安全（围栏/标识/通道/照明/灭火器），输入场景描述返回检测结果

### 步骤2：使用langgraph.prebuilt.create_react_agent创建Agent

### 步骤3：实现chat()函数通过agent.invoke()获取回答

### 步骤4：构建FastAPI后端 + Vue前端

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

- 安全距离的阈值如何根据电压等级动态调整？
- PPE检测的误报率如何降低？多工具交叉验证能起什么作用？
- 如何将检测结果生成结构化的安全检查报告？