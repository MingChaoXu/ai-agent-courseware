# 招投标智能助手

## 项目说明

招投标智能助手是一个完整的招标公告采集与处理平台，覆盖6个数据源，实现从公告采集→AI字段提取→客户匹配→Excel导出的全流程自动化。本文件是代码实现的技术文档，包含架构设计、模块说明和API接口。

## 项目结构

```
ex21_bidding_assistant/
├── backend/
│   ├── main.py                     # FastAPI入口，任务管理/文件管理/调度/搜索
│   ├── pipeline_v3.py              # Pipeline编排（Phase1采集 + Phase2处理）
│   ├── process.py                  # LLM信息提取（DeepSeek API + CircuitBreaker）
│   ├── config.py                   # 持久化配置（阈值/调度/AI核对）
│   ├── history.py                  # 历史记录管理（增量去重参考）
│   ├── merge.py                    # 文件合并（按文件/按时间）
│   ├── search.py                   # 关键词全文搜索
│   ├── health.py                   # 采集来源健康检查
│   ├── scheduler.py                # 定时任务调度器
│   ├── requirements.txt            # Python依赖
│   ├── collectors/                 # 6个数据源采集器
│   │   ├── __init__.py
│   │   ├── get_gov.py              # 苏州市政府采购-招标公告
│   │   ├── get_gov2.py             # 苏州市政府采购-采购意向
│   │   ├── get_jc.py               # 金采平台
│   │   ├── get_public.py           # 公共资源平台
│   │   ├── get_js.py               # 江苏省政府采购-招标公告
│   │   └── get_js2.py              # 江苏省政府采购-采购意向
│   ├── data/                       # 运行时数据目录
│   │   ├── phase1/                 # Phase1采集结果（JSON）
│   │   └── phase2/                 # Phase2处理结果（Excel）
│   └── kehu-0619.xlsx              # 客户清单（客户名称/客户经理/bu名称）
├── frontend/
│   └── index.html                  # Vue 3 CDN单页应用
├── skill/
│   ├── SKILL.md
│   └── tools/tool.py               # CLI + TeleAgent工具函数
├── EXERCISE.md
└── PROJECT_README.md
```

## 后端架构

### 模块1：数据采集（collectors/）

6个采集器使用Selenium + BeautifulSoup4从政府/公共资源平台采集招标公告：

| 采集器 | 数据源 | 采集内容 |
|--------|--------|---------|
| `get_gov` | 苏州市政府采购平台 | 招标公告 |
| `get_gov2` | 苏州市政府采购平台 | 采购意向 |
| `get_jc` | 金采平台 | 公告 |
| `get_public` | 公共资源平台 | 公告 |
| `get_js` | 江苏省政府采购平台 | 招标公告（公开招标） |
| `get_js2` | 江苏省政府采购平台 | 采购意向 |

每个采集器输出中间JSON文件到`data/`目录，合并后自动删除中间文件。

### 模块2：AI信息提取（process.py）

调用DeepSeek API逐条提取结构化字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `amount` | 预算金额 | 150.00万 |
| `is_it` | 采购品目 | 工程类-市政工程 |
| `public_due` | 公告截止时间 | 2026-08-01 |
| `result_due` | 结果截止时间 | 2026-08-15 |
| `tenderer` | 招标人 | 苏州市交通局 |

**熔断器机制**（`CircuitBreaker`）：
- CLOSED → 连续失败5次 → OPEN（快速失败，不调用API）
- OPEN → 冷却60秒 → HALF_OPEN（允许一次试探）
- HALF_OPEN → 成功 → CLOSED / 失败 → OPEN

### 模块3：Pipeline编排（pipeline_v3.py）

两阶段流水线：

```
Phase 1: 采集
  6个采集器并行 → 合并 → 去重 → 保存JSON
  输出: data/phase1/phase1_collected_<timestamp>.json

Phase 2: 处理
  读取JSON → 调用LLM提取字段 → 客户匹配 → 导出Excel
  输出: data/phase2/phase2_extracted_<timestamp>.xlsx
```

**客户匹配逻辑**：
1. 读取`kehu-0619.xlsx`客户清单
2. 对每条公告，使用`SequenceMatcher`计算与客户名称的相似度
3. 相似度 ≥ 阈值（默认0.70）则匹配成功
4. 可选：调用LLM对匹配结果进行二次核对（`ai_verify`配置项）

**增量模式**：
- `run_phase2_incremental()`: 跳过已分析的URL/标题
- `run_full_incremental()`: 增量采集 + 增量处理

### 模块4：Web服务（main.py）

FastAPI后端提供完整的管理界面：

**任务管理**：
- 5种任务类型：`phase1`/`phase2`/`full`/`phase2_incremental`/`full_incremental`
- 后台线程异步执行，`StreamCapture`捕获stdout/stderr到日志
- 任务持久化到`data/tasks.json`，支持历史恢复
- 内置调度器`PipelineScheduler`，可配置间隔自动触发

**API接口**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 前端页面 |
| GET | /api/tasks | 任务列表（支持状态/类型过滤） |
| POST | /api/tasks/{task_type} | 创建任务 |
| GET | /api/tasks/{task_id} | 任务详情 |
| DELETE | /api/tasks/{task_id} | 删除任务 |
| POST | /api/tasks/{task_id}/stop | 停止任务 |
| GET | /api/tasks/{task_id}/logs | 任务日志（支持分页/级别过滤） |
| GET | /api/tasks/{task_id}/report | 任务报告 |
| GET | /api/tasks/{task_id}/files | 任务输出文件 |
| GET | /api/files | 文件列表（支持分类过滤） |
| GET | /api/files/{category}/{filename} | 下载文件 |
| DELETE | /api/files/{category}/{filename} | 删除文件 |
| POST | /api/upload | 上传文件 |
| GET | /api/search | 关键词搜索 |
| POST | /api/merge | 合并文件 |
| GET | /api/scheduler | 调度器状态 |
| PUT | /api/scheduler | 更新调度器配置 |
| POST | /api/scheduler/toggle | 切换调度器开关 |
| POST | /api/scheduler/run | 立即触发调度 |
| GET | /api/health | 健康检查 |
| GET | /api/stats | 全局统计 |
| GET | /api/config | 配置信息（脱敏） |
| GET | /api/history | 任务历史 |
| GET | /api/phases | 流水线阶段信息 |

## 前端说明

Vue 3 CDN单页应用，6个功能视图：

**执行视图**：任务创建（5种类型选择）+ 任务列表 + 实时日志查看（级别过滤/暂停轮询）

**采集文件视图**：Phase1 JSON文件管理（上传/下载/预览/删除）

**处理文件视图**：Phase1→Phase2处理 + Phase2 Excel管理 + 文件合并（按选中/按时间范围）

**定时任务视图**：调度器配置（启用/禁用/立即执行）

**关键词查询视图**：全文搜索 + 结果高亮 + 详情查看

**配置视图**：匹配阈值滑块 + 调度开关 + AI核对开关 + 系统信息

## Skill说明

封装为7个tool函数：
- `bidding_run_pipeline`: 运行完整流水线（采集+处理）
- `bidding_run_phase1`: 仅运行Phase1采集
- `bidding_run_phase2`: 仅运行Phase2处理
- `bidding_search`: 关键词搜索采集数据
- `bidding_list_files`: 列出Phase1/Phase2文件
- `bidding_health_check`: 系统健康检查
- `bidding_get_config`: 获取当前配置

## 快速启动

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
export SILICONFLOW_API_KEY="your-api-key"
export HEADLESS=1  # 无头模式运行Selenium

# 3. 放置客户清单
# 将 kehu-0619.xlsx 放到 backend/ 目录下

# 4. 启动后端
python main.py
# 访问 http://localhost:8200
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SILICONFLOW_API_KEY` | DeepSeek API密钥 | （必填） |
| `HEADLESS` | Selenium无头模式 | 0 |
| `CHROMEDRIVER_PATH` | ChromeDriver路径 | 自动检测 |
| `SILICONFLOW_VL_API_KEY` | 视觉模型API密钥（采集器截图识别） | （可选） |

## 技术栈

- **采集**: Selenium 4 + BeautifulSoup4 + ChromeDriver
- **AI提取**: DeepSeek API（OpenAI兼容协议）+ CircuitBreaker熔断器
- **客户匹配**: difflib.SequenceMatcher + 可选LLM核对
- **后端**: FastAPI + Uvicorn + 后台线程
- **前端**: Vue 3 (CDN) + 原生CSS
- **数据**: JSON（Phase1）+ Excel/openpyxl（Phase2）