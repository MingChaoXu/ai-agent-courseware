## 课题名称

政务通报智能生成

## 学习目标

- 掌握PydanticOutputParser实现政务通报的结构化生成

## 项目概述

政务通报生成助手，生成包含事由/经过/结果/后续措施的规范通报。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义Pydantic模型

  - `GovernanceBrief`: title, category(突发事件/日常工作/政策通知/其他), background, process, result, follow_up, policy_basis

### 步骤2：使用PydanticOutputParser构建结构化输出Chain

### 步骤3：配置fallback_chain处理解析失败

### 步骤4：System Prompt中注入政务通报格式规范

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

- 如何根据事件类型（突发事件/日常工作/政策通知）调整生成风格？
- 政策依据字段如何保证准确性？LLM是否会编造法规条文？
- 政务通报的语言风格如何通过Prompt控制？