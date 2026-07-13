## 课题名称

人事制度智能审查

## 学习目标

- 掌握PydanticOutputParser实现人事制度合规性审查的结构化输出

## 项目概述

人事制度审查助手，审查5个维度（劳动法合规/制度完整/条款公平/操作可行/风险识别）。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义Pydantic模型

  - `HRReviewResult`: compliance_status(合规/部分合规/不合规), issues, missing_items, recommendations, summary

### 步骤2：使用PydanticOutputParser构建结构化输出Chain

### 步骤3：配置fallback_chain处理解析失败

### 步骤4：System Prompt中注入劳动法合规审查规则

### 步骤5：构建FastAPI后端 + Vue前端

## 技术栈

- `PydanticOutputParser`（结构化输出解析）
- `ChatPromptTemplate`（提示模板）
- LCEL（管道式Chain组装）
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 对话式交互界面，用户输入文本后返回AI分析结果
- 结构化JSON输出，前端渲染为卡片式展示

## 提示与思考

- 合规状态判断（合规/部分合规/不合规）的依据是什么？LLM如何做出判断？
- 如何结合记忆机制实现审查标准的持续学习？
- 制度缺失项的识别如何避免漏报？Prompt设计有什么技巧？