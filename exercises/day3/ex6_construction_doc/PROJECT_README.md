# 施工文档智能生成

## 项目说明

施工文档生成助手，支持工程概况/施工方案/安全措施/质量控制等章节。本文件是代码实现的技术文档，包含架构设计、API说明和代码细节。

## 项目结构

```
ex6_construction_doc/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── agent/agent.py
│   ├── api/chat.py
│   ├── api/health.py
│   └── models/schemas.py
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

### Chain架构

使用`ChatPromptTemplate + LLM + StrOutputParser`构建简单的LCEL Chain。

`chat()`函数调用`agent.invoke()`返回LLM生成的文本。

### API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/chat | 对话/分析接口 |

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

封装为单个tool函数，支持CLI调用（chat/health两个命令）。

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