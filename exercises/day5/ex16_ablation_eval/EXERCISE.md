## 课题名称

智能体消融评估

## 学习目标

- 掌握消融实验设计方法，评估Agent各组件（System Prompt/工具描述/语气风格）对性能的贡献

## 项目概述

AI Agent评估分析助手，帮助设计和执行消融实验。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义对比数据

  - `完整Agent`: 所有组件齐全（baseline）（优势: 性能最优, 劣势: 成本最高）
  - `去除SystemPrompt`: 去掉系统提示词（优势: 节省Token, 劣势: 输出质量下降明显）
  - `去除工具描述`: 去掉工具描述信息（优势: 减少Token, 劣势: 工具调用准确率下降）
  - `非正式语气`: 系统提示改为口语化（优势: 更自然, 劣势: 专业性和规范性下降）

### 步骤2：使用ChatPromptTemplate + StrOutputParser构建分析Chain

### 步骤3：chat()函数将对比数据注入context

- chat()函数将对比数据注入context，让LLM基于参考信息回答

### 步骤4：设计评估指标：准确率/完成率/Token消耗/延迟

### 步骤5：构建FastAPI后端 + Vue前端

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

- 消融实验的baseline如何选择？如何控制变量？
- Token消耗和输出质量之间如何权衡？
- 如何自动化执行多组消融实验并生成对比报告？