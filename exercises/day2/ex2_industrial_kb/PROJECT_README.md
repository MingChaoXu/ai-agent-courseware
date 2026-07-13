# 工业运维知识库检索

## 项目说明

工业设备运维知识助手，回答格式：故障现象 → 可能原因 → 处理步骤 → 预防措施。本文件是代码实现的技术文档，包含架构设计、API说明和代码细节。

## 项目结构

```
ex2_industrial_kb/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── agent/agent.py
│   ├── api/chat.py
│   ├── api/health.py
│   ├── models/schemas.py
│   └── api/knowledge.py
├── frontend/
│   └── index.html          # Vue 3 CDN 单页应用
├── skill/
│   ├── SKILL.md             # Skill文档
│   └── tools/
│       └── tool.py          # TeleAgent Skill工具
├── data/                    # 测试数据
├── EXERCISE.md              # 学生任务要求
├── PROJECT_README.md        # 本文件
└── .env.example             # 环境变量模板
```

## 后端架构

### RAG架构

**KnowledgeBase类**封装了向量知识库的全部操作：
- `upload_text()`: 文档上传 → RecursiveCharacterTextSplitter分块 → FAISS索引
- `search()`: 向量相似度检索，返回top_k个相关文档块
- `save_index()` / `load_index()`: FAISS索引持久化（处理非ASCII路径问题）
- `load_default_data()`: 启动时自动加载默认数据

**RAG Chain流程**：用户问题 → FAISS检索 → 拼接context → ChatPromptTemplate → LLM生成回答

**ConversationMemory**: 滑动窗口对话历史管理，保留最近6轮对话。

### API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/chat | RAG问答（含来源文档） |
| GET | /api/knowledge/documents | 知识库文档列表 |
| POST | /api/knowledge/upload | 上传文档到知识库 |
| POST | /api/knowledge/search | 向量检索测试 |
| POST | /api/knowledge/reload | 重新加载知识库 |

### 关键文件说明

- `agent/agent.py`: 核心Agent/Chain逻辑，定义Pydantic模型、工具函数、Chain工厂
- `api/chat.py`: 对话接口，调用agent并返回结果
- `api/health.py`: 健康检查接口
- `models/schemas.py`: Pydantic请求/响应模型（ChatRequest/ChatResponse/HealthResponse）
- `config.py`: 从.env读取LLM配置（API Key/Model/Base URL）
- `main.py`: FastAPI入口，注册路由、初始化Agent、CORS配置

## 前端说明

Vue 3 CDN单页应用，无需构建工具。主要功能：
- 对话式交互界面
- 文本回答展示
- 样本快速选择（嵌入测试数据）
- 健康状态实时显示

## Skill说明

封装为单个tool函数，支持CLI调用（chat/health两个命令），health返回知识库chunk数量。

## 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env填入LLM API配置

# 2. 安装依赖
pip install langchain langchain-openai langgraph faiss-cpu python-dotenv fastapi uvicorn

# 3. 启动后端
cd backend
python main.py
# 访问 http://localhost:8000
```

## 技术栈

- **LLM框架**: LangChain 1.x + LangGraph
- **后端**: FastAPI + Uvicorn
- **前端**: Vue 3 (CDN)
- **LLM接口**: OpenAI兼容协议