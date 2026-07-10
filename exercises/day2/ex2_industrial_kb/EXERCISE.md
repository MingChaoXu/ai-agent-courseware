## 课题名称

工业知识库检索

## 学习目标

- 巩固LCEL RAG构建能力
- 掌握检索参数调优方法
- 理解不同top_k对检索质量的影响

## 任务要求

### 步骤1：构建工业运维RAG系统

- 加载 `data/industrial_kb.json`
- 按照ex1的流程构建完整的RAG链（分块 → 嵌入 → FAISS索引 → LCEL管道）

### 步骤2：测试知识库问答质量

- 用工业领域问题测试系统（如设备故障诊断、运维规范等）
- 评估回答的准确性和完整性

### 步骤3：检索参数调优实验

- 分别设置 `top_k=1`、`top_k=3`、`top_k=5`
- 对同一问题对比三种参数下的回答质量差异
- 分析top_k增大时回答是变好还是变差，为什么

## 技术栈

- LangChain 1.x（同ex1的技术栈）
- `ChatOpenAI`、`ChatPromptTemplate`、`FAISS`、`OpenAIEmbeddings`、`RecursiveCharacterTextSplitter`、`StrOutputParser`、`RunnablePassthrough`

## 输入数据

- `data/industrial_kb.json`（5篇工业运维知识文档）

## 预期输出

- 不同top_k下同一问题的回答对比
- 参数选择分析（top_k取何值时效果最优，原因是什么）

## 提示与思考

- top_k越大越好吗？过多的无关上下文会如何影响LLM生成？
- 工业领域文档和政务FAQ在分块策略上是否需要不同处理？
- 如果知识库中没有对应答案，top_k调大能否解决问题？