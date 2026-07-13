# 智能体消融评估

## 项目说明

AI Agent评估分析助手，帮助设计和执行消融实验。本文件是代码实现的技术文档，包含架构设计、API说明和代码细节。

## 项目结构

```
ex16_ablation_eval/
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

### 对比实验架构

在代码中预定义对比数据（`COMPARISON_DATA`列表），`chat()`函数将对比数据注入到LLM的context中：

- 完整Agent: 所有组件齐全（baseline）（优势: 性能最优, 劣势: 成本最高）
- 去除SystemPrompt: 去掉系统提示词（优势: 节省Token, 劣势: 输出质量下降明显）
- 去除工具描述: 去掉工具描述信息（优势: 减少Token, 劣势: 工具调用准确率下降）
- 非正式语气: 系统提示改为口语化（优势: 更自然, 劣势: 专业性和规范性下降）

**Chain组装**：`ChatPromptTemplate → LLM → StrOutputParser`

LLM基于注入的对比数据回答用户问题，实现教学式的对比分析。

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