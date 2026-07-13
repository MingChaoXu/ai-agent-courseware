## 课题名称

综合方案路演Agent

## 学习目标

- 掌握多Agent协作实现综合方案路演（场景分析/技术方案/Demo演示/商业价值）

## 项目概述

4个Agent按路演评分权重协作：scenario_agent(20%) + solution_agent(30%) + demo_agent(30%) + value_agent(20%)。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义各Agent的LCEL Chain

  - `scenario_agent`: 分析业务场景痛点、用户需求、现有方案不足（权重20%）
  - `solution_agent`: 输出技术架构、核心算法、数据流程（权重30%）
  - `demo_agent`: 生成可交互的演示流程（权重30%）
  - `value_agent`: 量化ROI、社会效益、推广价值（权重20%）

### 步骤2：create_agent()返回包含4条Chain的字典

### 步骤3：chat()函数依次调用4条Chain

- chat()函数依次调用4条Chain，按评分权重组织输出

### 步骤4：构建FastAPI后端 + Vue前端

- 构建FastAPI后端 + Vue前端，展示路演全流程

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

- 路演的4个环节如何串联？前一个Agent的输出如何传递给下一个？
- 评分权重（20%/30%/30%/20%）如何确定？是否需要动态调整？
- 如何生成交互式Demo而非纯文本输出？