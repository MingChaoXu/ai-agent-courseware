## 课题名称

工业运维知识库检索

## 学习目标

- 掌握RAG（检索增强生成）全流程，理解FAISS向量检索与top_k参数调优

## 项目概述

工业设备运维知识助手，回答格式：故障现象 → 可能原因 → 处理步骤 → 预防措施。构建FastAPI后端 + Vue前端的完整全栈项目，通过本课题掌握相关技术的实战应用。

## 任务要求

### 步骤1：构建知识库

- 使用OpenAIEmbeddings将文档向量化
- 使用FAISS构建向量索引
- 使用RecursiveCharacterTextSplitter分块（chunk_size=800, overlap=80）

### 步骤2：实现KnowledgeBase类：upload_text()上传文档、search()向量检索、save_index()/load_index()持久化

### 步骤3：使用RecursiveCharacterTextSplitter对文档分块（chunk_size=800, overlap=80）

### 步骤4：组装RAG Chain：检索相关文档 → 拼接context → ChatPromptTemplate → LLM生成

### 步骤5：实现ConversationMemory对话历史管理（滑动窗口）

### 步骤6：支持top_k参数调节检索数量（1/3/5）

- 支持top_k参数调节检索数量（1/3/5），对比检索效果

### 步骤7：构建FastAPI后端 + Vue前端（含知识库管理侧边栏）

## 技术栈

- `OpenAIEmbeddings` + `FAISS`（向量检索）
- `RecursiveCharacterTextSplitter`（文档分块）
- LCEL RAG Chain
- FastAPI + Vue 3 CDN

## 输入数据

- 测试样本位于 `data/` 目录下
- 运行后可通过前端界面选择样本快速体验

## 预期输出

- 对话式交互界面，用户输入文本后返回AI分析结果
- LLM生成的文本回答

## 提示与思考

- chunk_size和overlap的大小如何影响检索精度？
- top_k=1和top_k=5在什么场景下各有优势？
- FAISS索引持久化到磁盘后，如何处理路径中的非ASCII字符问题？