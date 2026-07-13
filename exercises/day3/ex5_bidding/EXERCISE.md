## 课题名称

招标文件智能分析

## 学习目标

- 掌握PydanticOutputParser实现招标文件的结构化分析

## 项目概述

招标文件分析助手，分析6个维度（项目信息/资格要求/技术要求/评分标准/截止时间/风险提示）。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义Pydantic模型

  - `BiddingAnalysisResult`: project_info, qualification_req, technical_summary, scoring_criteria, deadline_info, risk_alerts, recommendations

### 步骤2：使用PydanticOutputParser构建结构化输出Chain

### 步骤3：配置fallback_chain处理解析失败

### 步骤4：System Prompt中注入招标文件分析规则

### 步骤5：构建FastAPI后端 + Vue前端（含招标样本选择卡片）

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

- 如何从非结构化的招标文件中提取结构化信息？Prompt设计有什么技巧？
- 评分标准分析如何量化？LLM能准确计算得分吗？
- 如果招标文件很长（超过上下文窗口），应该如何处理？