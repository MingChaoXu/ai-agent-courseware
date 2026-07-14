## 课题名称

招投标智能助手

## 学习目标

- 掌握Selenium自动化采集技术，实现多源招标公告数据采集（6个政府/公共资源平台）
- 掌握LLM结构化信息提取，将非结构化招标公告文本提取为结构化字段（金额/品目/公告截止/结果截止/招标人）
- 掌握两阶段Pipeline架构设计（Phase1采集 → Phase2处理），实现任务异步执行、状态追踪和日志收集
- 掌握客户智能匹配技术（SequenceMatcher相似度 + LLM二次核对 + 熔断器容错）

## 项目概述

招投标智能助手是一个完整的招标公告采集与处理平台，覆盖6个数据源（苏州市政府采购、江苏省政府采购、金采平台、公共资源平台），实现从公告采集→去重→AI字段提取→客户匹配→Excel导出的全流程自动化。构建FastAPI后端（任务管理/文件管理/定时调度/搜索/合并）+ Vue 3前端（6个功能视图）的完整全栈项目。

## 任务要求

### 步骤1：实现数据采集模块（collectors/）

  - 6个采集器分别采集不同数据源：
    - `get_gov.py`: 苏州市政府采购平台「招标公告」（Selenium）
    - `get_gov2.py`: 苏州市政府采购平台「采购意向」（Selenium + requests）
    - `get_jc.py`: 金采平台公告
    - `get_public.py`: 公共资源平台公告
    - `get_js.py`: 江苏省政府采购平台「招标公告」
    - `get_js2.py`: 江苏省政府采购平台「采购意向」
  - 每个采集器输出中间JSON文件到`data/`目录，格式：`intermediate_<source>_<timestamp>.json`
  - 支持`HEADLESS`环境变量控制无头模式，`CHROMEDRIVER_PATH`指定驱动路径

### 步骤2：实现AI信息提取模块（process.py）

  - 调用DeepSeek API（`https://api.deepseek.com/chat/completions`，模型`deepseek-v4-flash`）
  - 逐条提取结构化字段：`amount`（金额）、`is_it`（品目）、`public_due`（公告截止）、`result_due`（结果截止）、`tenderer`（招标人）
  - 实现`CircuitBreaker`熔断器：连续失败5次进入OPEN状态，冷却60秒后HALF_OPEN试探
  - API Key通过环境变量`SILICONFLOW_API_KEY`读取

### 步骤3：实现Pipeline编排模块（pipeline_v3.py）

  - `run_phase1()`: 调用6个采集器→合并去重→保存到`data/phase1/phase1_collected_<timestamp>.json`
  - `run_phase2(input_file)`: 读取Phase1数据→调用`process.py`提取字段→客户匹配→导出Excel到`data/phase2/`
  - `run_phase2_incremental()`: 增量处理，跳过已分析记录
  - 客户匹配：读取`kehu-0619.xlsx`，使用`SequenceMatcher`计算相似度，超过阈值（默认0.70）则匹配，可选AI二次核对

### 步骤4：构建FastAPI后端（main.py）

  - 任务管理：创建/查看/停止/删除任务，5种任务类型（phase1/phase2/full/phase2_incremental/full_incremental）
  - 异步执行：后台线程执行任务，实时日志收集（StreamCapture捕获stdout/stderr）
  - 文件管理：Phase1文件(JSON)和Phase2文件(Excel)的上传/下载/删除/预览
  - 定时调度：内置`PipelineScheduler`，支持启用/禁用/配置间隔/立即触发
  - 搜索：跨Phase1/Phase2数据的关键词全文搜索
  - 合并：按选中文件或时间范围合并数据

### 步骤5：构建Vue 3前端（frontend/index.html）

  - 6个功能视图：
    - 执行：任务创建（5种类型）+ 任务列表 + 实时日志查看
    - 采集文件：Phase1 JSON文件管理（上传/下载/预览/删除）
    - 处理文件：Phase1→Phase2处理 + Phase2 Excel管理 + 文件合并
    - 定时任务：调度配置（启用/禁用/立即执行）
    - 关键词查询：全文搜索 + 结果高亮
    - 配置：匹配阈值/调度开关/AI核对开关

## 技术栈

- **采集模块**: Selenium + BeautifulSoup4 + ChromeDriver
- **AI提取**: DeepSeek API（OpenAI兼容协议）+ CircuitBreaker熔断器
- **客户匹配**: difflib.SequenceMatcher + 可选LLM二次核对
- **后端**: FastAPI + Uvicorn + 后台线程
- **前端**: Vue 3 (CDN) + 原生CSS
- **数据存储**: JSON（Phase1）+ Excel/openpyxl（Phase2）

## 输入数据

- 采集数据来源：6个政府/公共资源网站（实时采集）
- 客户清单：`kehu-0619.xlsx`（含客户名称、客户经理、bu名称三列）
- 配置文件：`data/config.json`（匹配阈值、调度开关、AI核对开关）

## 预期输出

- Phase1输出：`data/phase1/phase1_collected_<timestamp>.json`（采集公告列表）
- Phase2输出：`data/phase2/phase2_extracted_<timestamp>.xlsx`（结构化字段 + 客户匹配结果）
- 前端界面：任务执行面板（实时日志）+ 文件管理 + 定时调度 + 搜索 + 配置

## 提示与思考

- 为什么需要熔断器？如果API持续失败，不加熔断器会发生什么？（提示：避免雪崩效应，快速失败保护系统）
- SequenceMatcher的相似度阈值0.70意味着什么？调高/调低有什么影响？（提示：调高减少误匹配但可能漏匹配，调低增加召回率但精度下降）
- 增量处理与全量处理有什么区别？为什么需要增量模式？（提示：避免重复处理已分析公告，节省API调用成本）
- Phase1和Phase2分离有什么好处？（提示：采集和处理可独立运行，采集失败不影响已有数据处理）