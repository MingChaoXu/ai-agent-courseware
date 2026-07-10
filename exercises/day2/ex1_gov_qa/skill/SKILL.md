# 政务服务智能问答技能

## 简介

基于 RAG（检索增强生成）的政务服务问答技能，可安装到 TeleAgent 智能体平台。使用 FAISS 向量知识库 + LangChain RAG Chain，为办事群众提供准确、有据可查的政务咨询服务。

覆盖业务领域：户籍、身份证、居住证、社保、医保、生育保险、公积金、不动产登记、婚姻登记、无犯罪记录证明等。

## 技能工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `gov_qa_answer` | 根据知识库回答政务问题 | `question`（问题）, `conversation_id`（可选，多轮对话ID） |
| `gov_qa_search` | 搜索知识库相关文档 | `query`（关键词）, `top_k`（返回条数，默认5） |
| `gov_qa_upload` | 上传文本到知识库 | `title`（标题）, `content`（内容） |
| `gov_qa_upload_file` | 上传文件到知识库 | `file_path`（文件路径，支持 .txt/.md/.json） |
| `gov_qa_list` | 列出知识库已有文档 | 无 |
| `gov_qa_clear` | 清除对话历史 | `conversation_id`（对话ID） |

## 安装方式

将 `skill/` 目录安装到 TeleAgent 技能目录：

```bash
# 方式一：符号链接
ln -s /path/to/ex1_gov_qa/skill ~/.config/TeleAgent/skills/gov_qa

# 方式二：直接复制
cp -r /path/to/ex1_gov_qa/skill ~/.config/TeleAgent/skills/gov_qa
```

安装后在 TeleAgent 中可直接对话使用：

- "新生儿落户需要什么材料？"
- "社保怎么从外地转过来？"
- "公积金贷款最高额度是多少？"
- "居住证如何申请？"

## 环境配置

在项目根目录 `.env` 文件中配置：

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | LLM API 密钥 |
| `OPENAI_API_BASE` | LLM API 地址 |
| `OPENAI_MODEL_NAME` | 模型名称 |
| `EMBEDDING_MODEL_NAME` | Embedding 模型名称 |
| `EMBEDDING_API_KEY` | Embedding API 密钥 |
| `EMBEDDING_API_BASE` | Embedding API 地址 |

## 测试数据

| 文件 | 说明 |
|------|------|
| `data/gov_faq.json` | 50条真实政务FAQ（10大类别），启动时自动加载 |
| `data/test_户政业务网上办理指引.md` | 户政业务网上办理指南（广州番禺） |
| `data/test_居住证申领指南.md` | 居住证申领流程指南（凉山州） |
| `data/test_住房公积金贷款指南.md` | 公积金贷款购房指南（韶关市） |
| `data/test_社会保险参保办事指南.md` | 社保参保办事指南（淮北相山区） |

## 命令行测试

```bash
# 初始化知识库
python skill/tools/gov_qa.py init

# 提问
python skill/tools/gov_qa.py answer -q "新生儿落户需要什么材料？"

# 搜索知识库
python skill/tools/gov_qa.py search -q "公积金贷款"

# 列出已有文档
python skill/tools/gov_qa.py list

# 上传文件
python skill/tools/gov_qa.py upload-file -f data/test_居住证申领指南.md
```

## 架构

```
用户提问
    │
    ▼
┌──────────────────┐
│  FAISS 向量检索   │ ── Top-K 相似文档
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  RAG 提示模板     │ ── 注入上下文 + 对话历史 + 问题
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  LLM 生成回答     │ ── 严格依据检索内容作答
└──────────────────┘
    │
    ▼
回答内容 + 参考来源
```

## 与后端的关系

技能工具 (`skill/tools/gov_qa.py`) 直接复用后端 (`backend/`) 的核心模块：
- `agent/knowledge_base.py` — FAISS 向量库管理
- `agent/rag_chain.py` — RAG 检索链
- `agent/prompts.py` — 系统提示模板
- `config.py` — 环境配置

两者共享同一套 RAG 能力：后端提供 Web API（FastAPI），技能提供 TeleAgent 工具接口。
