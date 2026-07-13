# 电力安全CV检测Agent

## 项目说明

电力行业安全检测助手，使用PPE检测、安全距离检测和环境检测工具。本文件是代码实现的技术文档，包含架构设计、API说明和代码细节。

## 项目结构

```
ex13_cv_safety/
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

### Agent架构

使用LangGraph的`create_react_agent`构建ReAct Agent，核心组件：

- `ppe_check`: 检测人员PPE佩戴情况（安全帽/手套/鞋/服），输入场景描述返回检测结果
- `distance_check`: 检查人员与带电设备的安全距离，输入场景描述返回距离检测结果
- `environment_check`: 检查作业环境安全（围栏/标识/通道/照明/灭火器），输入场景描述返回检测结果

**执行流程**：用户输入 → LLM推理(Thought) → 选择工具(Action) → 执行工具获取结果(Observation) → 循环直到得出最终答案。

`agent.invoke({messages: [("user", question)]})` 返回消息列表，取最后一条作为最终回答。

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
- 工具调用过程展示
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