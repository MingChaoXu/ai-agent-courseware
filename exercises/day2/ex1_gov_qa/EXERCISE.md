## 课题名称

政务服务智能问答

## 学习目标

- 掌握LCEL管道式组合
- 理解RAG全流程（检索 → 注入 → 生成）
- 学会用FAISS构建向量知识库

## 任务要求

### 步骤1：初始化ChatOpenAI

- 配置API Key和模型参数
- 发送一条测试消息，验证LLM连接正常

### 步骤2：定义RAG提示模板

- 使用 `ChatPromptTemplate` 定义提示模板
- 包含 `{context}` 和 `{question}` 两个占位符
- 在模板中指示LLM只根据context回答，不知道就说不知道

### 步骤3：构建FAISS向量索引

- 加载 `data/gov_faq.json`
- 使用 `RecursiveCharacterTextSplitter` 进行文本分块
- 使用 `OpenAIEmbeddings` 生成嵌入向量
- 构建FAISS索引并保存

### 步骤4：用LCEL管道组装RAG链

- 用管道操作符 `|` 组装：`rag_chain = retriever | prompt | llm | parser`
- 理解每个环节的数据流向

### 步骤5：多轮问答测试

- 测试知识库内的问题（应准确回答）
- 测试知识库外的问题（应拒绝编造）
- 验证RAG系统既准确又不幻觉

## 技术栈

- LangChain 1.x
- `ChatOpenAI`（LLM调用）
- `ChatPromptTemplate`（提示模板）
- `FAISS`（向量存储）
- `OpenAIEmbeddings`（嵌入模型）
- `RecursiveCharacterTextSplitter`（文本分块）
- `StrOutputParser`（输出解析）
- `RunnablePassthrough`（数据透传）

## 输入数据

- `data/gov_faq.json`（35条政务FAQ，覆盖户籍、社保、公积金、不动产6大类别）

## 预期输出

- 4个测试问题的回答，包含：
  - 知识库内问题：准确引用原文作答
  - 知识库外问题：明确表示未找到相关信息，不编造政策

## 提示与思考

- RAG的三个阶段（检索、注入、生成）各自解决什么问题？
- 如果检索到的上下文与问题无关，LLM会怎样？如何缓解？
- `FAISS` 的相似度搜索和关键词搜索有什么本质区别？