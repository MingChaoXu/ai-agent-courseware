## 课题名称

PCB质量AI检测Agent

## 学习目标

- 掌握LangGraph create_react_agent实现PCB电路板质量检测

## 项目概述

PCB电路板质量检测助手，使用缺陷检测、OCR识别和元件计数工具。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：定义工具函数

  - `defect_detect`: 检测PCB板焊接缺陷（连锡/偏移/划痕），输入图像描述返回缺陷类型和位置
  - `ocr_extract`: OCR识别PCB板丝印文字，输入图像描述返回型号/序列号/认证标识
  - `component_count`: 统计PCB板元件数量，输入图像描述返回元件统计结果

### 步骤2：使用langgraph.prebuilt.create_react_agent创建Agent

### 步骤3：实现chat()函数通过agent.invoke()获取回答

### 步骤4：对比三种多模态处理模式（NATIVE/EXTRACT/TOOL）在质量检测场景的应用

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

- Mock工具返回的是固定结果，如何替换为真实的CV模型API？
- Agent如何决定先调用哪个工具？工具描述如何影响选择？
- 多工具协作时，如何保证检测结果的一致性？