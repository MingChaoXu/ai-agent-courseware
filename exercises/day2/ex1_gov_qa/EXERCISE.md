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

## 全栈项目

本课题附带一个完整的全栈演示项目，将 `run.py` 中的 RAG Chain 封装为可交互的 Web 应用。

### 项目结构

```
ex1_gov_qa/
├── run.py              # 训练脚本（5步教程）
├── EXERCISE.md         # 本文件
├── PROJECT_README.md   # 全栈项目详细文档
├── .env.example        # API 配置模板
├── .gitignore
├── backend/            # FastAPI 后端
│   ├── main.py         # 入口：启动时加载知识库，挂载 API 路由
│   ├── config.py       # 配置项（LLM / Embedding / RAG 参数）
│   ├── agent/          # RAG 核心
│   │   ├── rag_chain.py        # RAGChain: retrieve → prompt → LLM → answer
│   │   ├── knowledge_base.py   # KnowledgeBase: FAISS 向量库管理
│   │   └── prompts.py          # 系统提示模板
│   ├── api/            # REST API
│   │   ├── chat.py     # POST /api/chat, DELETE /api/chat/{id}
│   │   ├── knowledge.py # GET/POST /api/knowledge/*
│   │   └── health.py   # GET /api/health
│   └── models/         # Pydantic 数据模型
├── frontend/           # Vue 3 单页应用（CDN）
│   └── index.html      # 侧边栏知识库管理 + 对话 + 来源卡片
├── data/               # 测试数据
│   └── gov_faq.json    # 50 条真实政务 FAQ（10 大类别）
└── skill/              # TeleAgent 技能包
    ├── SKILL.md        # 技能描述
    └── tools/gov_qa.py # GovQATool + CLI
```

### 快速启动

```bash
# 1. 配置 API
cp .env.example .env
# 编辑 .env 填入 API Key

# 2. 安装后端依赖
pip install -r backend/requirements.txt

# 3. 启动服务
cd backend
python main.py
# 浏览器打开 http://localhost:8000
```

### 技术架构

- **后端**: FastAPI + LangChain 1.x + FAISS
- **前端**: Vue 3 (CDN) + Tailwind CSS
- **技能**: TeleAgent Skill（可安装到智能体平台）
