# -*- coding: utf-8 -*-
"""
招标公告采集与处理流水线 - Web 后台服务 (FastAPI)
基于 FastAPI + 后台线程实现任务调度、日志收集、文件管理、报告统计。
"""
import os
import sys
import io
import json
import re
import time
import uuid
import threading
import traceback
import atexit
import signal
from datetime import datetime
from collections import deque
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request, UploadFile, File, Query, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保能导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PHASE1_DIR = os.path.join(DATA_DIR, "phase1")
PHASE2_DIR = os.path.join(DATA_DIR, "phase2")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
SCHEDULER_CONFIG_FILE = os.path.join(DATA_DIR, "scheduler.json")

for d in (PHASE1_DIR, PHASE2_DIR, UPLOAD_DIR):
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------------------
# 导入业务模块（容错：模块不存在时降级运行）
# ---------------------------------------------------------------------------
try:
    import pipeline_v3
except ImportError:
    pipeline_v3 = None
    print("[WARNING] pipeline_v3 模块未找到，任务执行将使用内置回退逻辑")

try:
    import config as _config
except ImportError:
    _config = None
    print("[WARNING] config 模块未找到")

try:
    import history as _history
except ImportError:
    _history = None
    print("[WARNING] history 模块未找到")

try:
    import scheduler as _scheduler
except ImportError:
    _scheduler = None
    print("[WARNING] scheduler 模块未找到，将使用内置调度器")

try:
    import merge as _merge
except ImportError:
    _merge = None
    print("[WARNING] merge 模块未找到")

try:
    import search as _search
except ImportError:
    _search = None
    print("[WARNING] search 模块未找到")

try:
    import health as _health
except ImportError:
    _health = None
    print("[WARNING] health 模块未找到")


# ===========================================================================
# TaskLogger — 线程安全的任务日志收集器
# ===========================================================================
class TaskLogger:
    """任务日志记录器，线程安全地收集日志条目。"""

    def __init__(self, task_id: str, max_entries: int = 5000):
        self.task_id = task_id
        self._entries: deque = deque(maxlen=max_entries)
        self._lock = threading.Lock()

    def log(self, message: str, level: str = "info"):
        """记录一条日志。"""
        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
        }
        with self._lock:
            self._entries.append(entry)

    def get_logs(self, after: int = 0) -> List[dict]:
        """获取日志条目，after 为起始索引。"""
        with self._lock:
            entries = list(self._entries)
        if after > 0 and after < len(entries):
            return entries[after:]
        return entries

    def get_log_text(self) -> str:
        """获取纯文本格式的全部日志。"""
        with self._lock:
            entries = list(self._entries)
        return "\n".join(
            f"[{e['time']}] [{e['level'].upper()}] {e['message']}" for e in entries
        )

    def clear(self):
        """清空日志。"""
        with self._lock:
            self._entries.clear()

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._entries)


# ===========================================================================
# StreamCapture — 捕获 stdout / stderr 并转发到 TaskLogger
# ===========================================================================
class StreamCapture:
    """上下文管理器：重定向 stdout/stderr 到 TaskLogger。"""

    def __init__(self, logger: TaskLogger):
        self.logger = logger
        self._buffer = ""
        self._orig_stdout = None
        self._orig_stderr = None

    def __enter__(self):
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr
        if self._buffer:
            self.logger.log(self._buffer.rstrip())
            self._buffer = ""
        return False

    def write(self, text: str):
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                self.logger.log(line.rstrip())

    def flush(self):
        if self._buffer:
            self.logger.log(self._buffer.rstrip())
            self._buffer = ""


# ===========================================================================
# Task — 任务数据模型
# ===========================================================================
class Task:
    """任务数据模型，封装状态、日志、结果和线程控制。"""

    def __init__(self, task_id: str, task_type: str, params: dict = None):
        self.id = task_id
        self.type = task_type
        self.params = params or {}
        self.status = "pending"          # pending | running | completed | failed | stopped
        self.progress = 0                # 0 ~ 100
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        self.error: Optional[str] = None
        self.result: Optional[dict] = None
        self.report: Optional[dict] = None
        self.files: List[str] = []
        self.logger = TaskLogger(task_id)
        self._stop_flag = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ---- 序列化 ----
    def to_dict(self) -> dict:
        """序列化为字典（用于 API 响应）。"""
        return {
            "id": self.id,
            "type": self.type,
            "params": self.params,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "result": self.result,
            "report": self.report,
            "files": self.files,
            "log_count": self.logger.count,
        }

    def to_persist_dict(self) -> dict:
        """序列化为持久化字典（包含日志）。"""
        d = self.to_dict()
        d["logs"] = self.logger.get_logs()
        return d

    @classmethod
    def from_persist_dict(cls, d: dict) -> "Task":
        """从持久化字典恢复任务。"""
        task = cls(d["id"], d["type"], d.get("params", {}))
        task.status = d.get("status", "completed")
        task.progress = d.get("progress", 0)
        task.created_at = d.get("created_at", task.created_at)
        task.started_at = d.get("started_at")
        task.finished_at = d.get("finished_at")
        task.error = d.get("error")
        task.result = d.get("result")
        task.report = d.get("report")
        task.files = d.get("files", [])
        for log_entry in d.get("logs", []):
            task.logger._entries.append(log_entry)
        return task

    # ---- 线程控制 ----
    def request_stop(self):
        """请求停止任务。"""
        self._stop_flag.set()

    @property
    def stop_requested(self) -> bool:
        return self._stop_flag.is_set()


# ===========================================================================
# TASKS 全局字典 & 线程锁
# ===========================================================================
TASKS: Dict[str, Task] = {}
_TASKS_LOCK = threading.Lock()


# ===========================================================================
# 任务持久化
# ===========================================================================
def _save_tasks_persist():
    """持久化所有任务到 JSON 文件。"""
    try:
        with _TASKS_LOCK:
            data = {tid: task.to_persist_dict() for tid, task in TASKS.items()}
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] 保存任务失败: {e}")


def _load_tasks_persist():
    """从 JSON 文件加载历史任务。"""
    if not os.path.exists(TASKS_FILE):
        return
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        loaded = 0
        with _TASKS_LOCK:
            for tid, task_data in data.items():
                # 跳过仍在 running 的任务（进程重启后无法恢复线程）
                if task_data.get("status") == "running":
                    task_data["status"] = "stopped"
                    task_data["error"] = "进程重启，任务中断"
                    task_data["finished_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                task = Task.from_persist_dict(task_data)
                TASKS[tid] = task
                loaded += 1
        print(f"[INFO] 已加载 {loaded} 个历史任务")
    except Exception as e:
        print(f"[ERROR] 加载任务失败: {e}")


def register_task(task: Task):
    """注册任务到全局字典并持久化。"""
    with _TASKS_LOCK:
        TASKS[task.id] = task
    _save_tasks_persist()


# ===========================================================================
# 报告解析
# ===========================================================================
def parse_phase1_report(report_data) -> dict:
    """解析 Phase1 报告数据，提取采集统计信息。"""
    result = {
        "total_collected": 0,
        "success_count": 0,
        "failed_count": 0,
        "sources": {},
        "date_range": {"start": None, "end": None},
        "items": [],
    }
    if not report_data:
        return result

    if isinstance(report_data, dict):
        result["total_collected"] = report_data.get("total", report_data.get("total_collected", 0))
        result["success_count"] = report_data.get("success", report_data.get("success_count", 0))
        result["failed_count"] = report_data.get("failed", report_data.get("failed_count", 0))
        result["sources"] = report_data.get("sources", {})
        result["date_range"] = report_data.get("date_range", result["date_range"])
        result["items"] = report_data.get("items", [])
        return result

    if isinstance(report_data, str):
        try:
            return parse_phase1_report(json.loads(report_data))
        except (json.JSONDecodeError, TypeError):
            lines = report_data.strip().split("\n")
            for line in lines:
                if "总计" in line or "total" in line.lower():
                    m = re.search(r"(\d+)", line)
                    if m:
                        result["total_collected"] = int(m.group(1))
                if "成功" in line or "success" in line.lower():
                    m = re.search(r"(\d+)", line)
                    if m:
                        result["success_count"] = int(m.group(1))
                if "失败" in line or "failed" in line.lower():
                    m = re.search(r"(\d+)", line)
                    if m:
                        result["failed_count"] = int(m.group(1))
            return result
    return result


def parse_phase2_report(report_data) -> dict:
    """解析 Phase2 报告数据，提取分析统计信息。"""
    result = {
        "total_analyzed": 0,
        "categories": {},
        "budget_ranges": {"0-10万": 0, "10-50万": 0, "50-100万": 0, "100万+": 0},
        "deadline_urgent": 0,
        "deadline_normal": 0,
        "deadline_long": 0,
        "items": [],
        "summary": "",
    }
    if not report_data:
        return result

    if isinstance(report_data, dict):
        result["total_analyzed"] = report_data.get("total_analyzed", report_data.get("total", 0))
        result["categories"] = report_data.get("categories", {})
        result["budget_ranges"] = report_data.get("budget_ranges", result["budget_ranges"])
        result["deadline_urgent"] = report_data.get("deadline_urgent", 0)
        result["deadline_normal"] = report_data.get("deadline_normal", 0)
        result["deadline_long"] = report_data.get("deadline_long", 0)
        result["items"] = report_data.get("items", [])
        result["summary"] = report_data.get("summary", "")
        return result

    if isinstance(report_data, str):
        try:
            return parse_phase2_report(json.loads(report_data))
        except (json.JSONDecodeError, TypeError):
            return result
    return result


def build_report(task: Task) -> dict:
    """构建完整报告，合并 Phase1 和 Phase2 统计。"""
    report = {
        "task_id": task.id,
        "task_type": task.type,
        "status": task.status,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "phase1": {},
        "phase2": {},
        "files": task.files,
        "summary": "",
    }

    if task.report:
        if isinstance(task.report, dict):
            p1_key = "phase1" if "phase1" in task.report else "phase1_report"
            p2_key = "phase2" if "phase2" in task.report else "phase2_report"
            if p1_key in task.report:
                report["phase1"] = parse_phase1_report(task.report[p1_key])
            if p2_key in task.report:
                report["phase2"] = parse_phase2_report(task.report[p2_key])
        else:
            report["phase1"] = parse_phase1_report(task.report)

    p1 = report["phase1"]
    p2 = report["phase2"]
    parts = []
    if p1.get("total_collected"):
        parts.append(f"采集 {p1['total_collected']} 条公告")
    if p1.get("success_count"):
        parts.append(f"成功 {p1['success_count']} 条")
    if p2.get("total_analyzed"):
        parts.append(f"分析 {p2['total_analyzed']} 条")
    report["summary"] = "，".join(parts) if parts else "无统计数据"
    return report


# ===========================================================================
# 文件管理辅助函数
# ===========================================================================
def list_files(directory: str, category: str) -> List[dict]:
    """列出目录中的文件信息。"""
    files = []
    if not os.path.exists(directory):
        return files
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            stat = os.stat(path)
            files.append({
                "name": name,
                "category": category,
                "size": stat.st_size,
                "size_human": _human_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "path": os.path.relpath(path, BASE_DIR),
            })
    return files


def _human_size(size: int) -> str:
    """将字节数转换为人类可读格式。"""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def find_latest_file(directory: str, prefix: str = "", suffix: str = ".json") -> Optional[str]:
    """查找目录中最新符合条件的文件路径。"""
    if not os.path.exists(directory):
        return None
    candidates = []
    for name in os.listdir(directory):
        if prefix and not name.startswith(prefix):
            continue
        if suffix and not name.endswith(suffix):
            continue
        full = os.path.join(directory, name)
        if os.path.isfile(full):
            candidates.append((os.path.getmtime(full), full))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def get_category_dir(category: str) -> Optional[str]:
    """根据分类名获取对应目录。"""
    mapping = {
        "phase1": PHASE1_DIR,
        "phase2": PHASE2_DIR,
        "uploads": UPLOAD_DIR,
        "data": DATA_DIR,
    }
    return mapping.get(category)


def load_json_file(filepath: str) -> Any:
    """安全加载 JSON 文件。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_json_file(filepath: str, data: Any) -> bool:
    """安全保存 JSON 文件。"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] 保存 JSON 失败: {e}")
        return False


# ===========================================================================
# 任务执行器
# ===========================================================================
def _run_phase1_task(task: Task, params: dict):
    """执行 Phase1 数据采集任务。"""
    logger = task.logger
    logger.log("=" * 60)
    logger.log(f"开始执行 Phase1 数据采集任务 (ID: {task.id})")
    logger.log(f"参数: {json.dumps(params, ensure_ascii=False)}")
    logger.log("=" * 60)

    task.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task.status = "running"
    _save_tasks_persist()

    try:
        sources = params.get("sources", ["gov"])
        days = params.get("days", 7)
        pages = params.get("pages", 3)

        all_results = []
        intermediate_files = []

        # 优先调用 pipeline_v3
        if pipeline_v3 and hasattr(pipeline_v3, "run_phase1"):
            logger.log("调用 pipeline_v3.run_phase1() ...")
            with StreamCapture(logger):
                result = pipeline_v3.run_phase1(
                    output_dir=PHASE1_DIR,
                    sources=sources,
                    days=days,
                    pages=pages,
                    task=task,
                )
            if isinstance(result, dict):
                all_results = result.get("items", [])
                if result.get("intermediate_file"):
                    intermediate_files.append(result["intermediate_file"])
                logger.log(f"pipeline_v3 返回 {len(all_results)} 条记录")
            elif isinstance(result, (list, tuple)) and result:
                all_results = result[0] if isinstance(result[0], list) else result
                if len(result) > 1 and isinstance(result[1], str):
                    intermediate_files.append(result[1])
        else:
            # 回退：直接调用采集器
            logger.log("pipeline_v3 不可用，尝试直接调用采集器...")
            from collectors import get_gov

            if "gov" in sources:
                logger.log("启动政府采购平台采集...")
                with StreamCapture(logger):
                    items, intermediate_file = get_gov.run()
                all_results.extend(items)
                intermediate_files.append(intermediate_file)
                logger.log(f"政府采购平台采集完成: {len(items)} 条")

        if task.stop_requested:
            task.status = "stopped"
            task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.log("任务已被用户停止", level="warning")
            _save_tasks_persist()
            return

        task.progress = 50

        # 保存采集结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(PHASE1_DIR, f"phase1_{timestamp}.json")
        report_data = {
            "total": len(all_results),
            "success": len([i for i in all_results if i.get("content")]),
            "failed": len([i for i in all_results if not i.get("content")]),
            "sources": {"gov": len(all_results)},
            "date_range": {
                "start": min((i.get("date", "") for i in all_results), default=""),
                "end": max((i.get("date", "") for i in all_results), default=""),
            },
            "items": [
                {
                    "title": i.get("title", ""),
                    "url": i.get("url", ""),
                    "date": i.get("date", ""),
                    "has_content": bool(i.get("content")),
                }
                for i in all_results
            ],
        }

        save_json_file(output_file, {"data": all_results, "report": report_data})
        logger.log(f"采集结果已保存: {output_file}")
        task.files.append(os.path.relpath(output_file, BASE_DIR))

        # 清理中间文件
        for imf in intermediate_files:
            try:
                if os.path.exists(imf):
                    os.remove(imf)
                    logger.log(f"已清理中间文件: {imf}")
            except Exception:
                pass

        task.progress = 100
        task.result = {
            "output_file": os.path.relpath(output_file, BASE_DIR),
            "total": len(all_results),
        }
        task.report = {"phase1": report_data}
        task.status = "completed"
        task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.log(f"Phase1 任务完成! 共采集 {len(all_results)} 条公告")

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.log(f"Phase1 任务失败: {e}", level="error")
        logger.log(traceback.format_exc(), level="error")

    _save_tasks_persist()


def _run_phase2_task(task: Task, params: dict):
    """执行 Phase2 智能分析任务。"""
    logger = task.logger
    logger.log("=" * 60)
    logger.log(f"开始执行 Phase2 智能分析任务 (ID: {task.id})")
    logger.log(f"参数: {json.dumps(params, ensure_ascii=False)}")
    logger.log("=" * 60)

    task.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task.status = "running"
    _save_tasks_persist()

    try:
        # 确定输入文件
        input_file = params.get("input_file")
        if input_file:
            input_path = input_file if os.path.isabs(input_file) else os.path.join(BASE_DIR, input_file)
        else:
            input_path = find_latest_file(PHASE1_DIR, prefix="phase1_", suffix=".json")

        if not input_path or not os.path.exists(input_path):
            raise FileNotFoundError("未找到 Phase1 数据文件，请先执行 Phase1 采集任务")

        logger.log(f"输入数据文件: {input_path}")
        raw = load_json_file(input_path)
        if raw is None:
            raise ValueError("输入数据文件解析失败")
        items = raw.get("data", raw) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            raise ValueError("输入数据格式不正确")
        logger.log(f"待分析公告数: {len(items)}")

        task.progress = 10

        # 优先调用 pipeline_v3
        if pipeline_v3 and hasattr(pipeline_v3, "run_phase2"):
            logger.log("调用 pipeline_v3.run_phase2() ...")
            with StreamCapture(logger):
                result = pipeline_v3.run_phase2(
                    input_dir=PHASE1_DIR,
                    output_dir=PHASE2_DIR,
                    input_file=input_path,
                    items=items,
                    model=params.get("model"),
                    task=task,
                )
            analyzed_items = result.get("items", []) if isinstance(result, dict) else []
            report_data = result.get("report", {}) if isinstance(result, dict) else {}
            output_file = result.get("output_file", "") if isinstance(result, dict) else ""
        else:
            # 回退：基于正则的基本分析
            logger.log("pipeline_v3 不可用，使用内置基本分析...")
            analyzed_items = []
            categories = {}
            budget_ranges = {"0-10万": 0, "10-50万": 0, "50-100万": 0, "100万+": 0}
            deadline_urgent = 0
            deadline_normal = 0
            deadline_long = 0

            total = len(items)
            for idx, item in enumerate(items):
                if task.stop_requested:
                    break

                title = item.get("title", "")
                content = item.get("content", "")

                # 提取预算金额
                budget = None
                budget_match = re.search(r"(?:预算|控制价|金额)[^0-9]*([\d.]+)\s*万", content)
                if budget_match:
                    budget = float(budget_match.group(1))

                # 提取截止时间
                deadline = None
                deadline_match = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", content)
                if deadline_match:
                    deadline = deadline_match.group(1).replace("年", "-").replace("月", "-").replace("/", "-")

                # 分类
                category = "其他"
                for cat, keywords in {
                    "工程": ["工程", "施工", "建设", "装修"],
                    "货物": ["采购", "设备", "物资", "货物"],
                    "服务": ["服务", "咨询", "评估", "审计"],
                }.items():
                    if any(k in title for k in keywords):
                        category = cat
                        break
                categories[category] = categories.get(category, 0) + 1

                # 预算区间
                if budget is not None:
                    if budget < 10:
                        budget_ranges["0-10万"] += 1
                    elif budget < 50:
                        budget_ranges["10-50万"] += 1
                    elif budget < 100:
                        budget_ranges["50-100万"] += 1
                    else:
                        budget_ranges["100万+"] += 1

                # 紧急程度
                if deadline:
                    try:
                        dl_date = datetime.strptime(deadline, "%Y-%m-%d").date()
                        days_left = (dl_date - datetime.now().date()).days
                        if days_left <= 7:
                            deadline_urgent += 1
                        elif days_left <= 30:
                            deadline_normal += 1
                        else:
                            deadline_long += 1
                    except ValueError:
                        pass

                analyzed_items.append({
                    "title": title,
                    "url": item.get("url", ""),
                    "date": item.get("date", ""),
                    "category": category,
                    "budget": budget,
                    "deadline": deadline,
                    "snippet": content[:300] if content else "",
                })

                task.progress = 10 + int(80 * (idx + 1) / total)
                if (idx + 1) % 10 == 0:
                    logger.log(f"已分析 {idx + 1}/{total} 条")

            report_data = {
                "total_analyzed": len(analyzed_items),
                "categories": categories,
                "budget_ranges": budget_ranges,
                "deadline_urgent": deadline_urgent,
                "deadline_normal": deadline_normal,
                "deadline_long": deadline_long,
                "items": [{"title": a["title"], "category": a["category"], "budget": a["budget"]} for a in analyzed_items],
                "summary": f"共分析 {len(analyzed_items)} 条公告",
            }
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(PHASE2_DIR, f"phase2_{timestamp}.json")

        if task.stop_requested:
            task.status = "stopped"
            task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.log("任务已被用户停止", level="warning")
            _save_tasks_persist()
            return

        # 保存分析结果
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(PHASE2_DIR, f"phase2_{timestamp}.json")

        save_json_file(output_file, {"data": analyzed_items, "report": report_data})
        logger.log(f"分析结果已保存: {output_file}")
        task.files.append(os.path.relpath(output_file, BASE_DIR))

        task.progress = 100
        task.result = {
            "output_file": os.path.relpath(output_file, BASE_DIR),
            "total_analyzed": len(analyzed_items),
        }
        task.report = {"phase2": report_data}
        task.status = "completed"
        task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.log(f"Phase2 任务完成! 共分析 {len(analyzed_items)} 条公告")

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.log(f"Phase2 任务失败: {e}", level="error")
        logger.log(traceback.format_exc(), level="error")

    _save_tasks_persist()


def _run_full_task(task: Task, params: dict):
    """执行完整流水线任务（Phase1 + Phase2）。"""
    logger = task.logger
    logger.log("=" * 60)
    logger.log(f"开始执行完整流水线任务 (ID: {task.id})")
    logger.log("=" * 60)

    task.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task.status = "running"
    _save_tasks_persist()

    try:
        # ---- Phase1 ----
        logger.log(">>> 阶段 1/2: 数据采集")
        _run_phase1_task(task, params)

        if task.status in ("failed", "stopped"):
            logger.log("Phase1 未成功，终止流水线", level="warning")
            return

        # 找到刚生成的 phase1 输出文件
        phase1_output = task.files[-1] if task.files else None
        if phase1_output:
            params = {**params, "input_file": phase1_output}

        # ---- Phase2 ----
        logger.log(">>> 阶段 2/2: 智能分析")
        # 重置状态以继续执行
        task.status = "running"
        task._stop_flag.clear()
        _save_tasks_persist()

        phase1_report = task.report.get("phase1", {}) if task.report else {}
        _run_phase2_task(task, params)

        # 合并报告
        if task.report:
            phase2_report = task.report.get("phase2", {})
            task.report = {"phase1": phase1_report, "phase2": phase2_report}

        logger.log("完整流水线任务完成!")

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.log(f"完整流水线任务失败: {e}", level="error")
        logger.log(traceback.format_exc(), level="error")

    _save_tasks_persist()


def _run_phase2_incremental_task(task: Task, params: dict):
    """执行增量分析任务（仅分析新增数据）。"""
    logger = task.logger
    logger.log("=" * 60)
    logger.log(f"开始执行增量分析任务 (ID: {task.id})")
    logger.log("=" * 60)

    task.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task.status = "running"
    _save_tasks_persist()

    try:
        # 收集已分析的 URL/title 集合
        analyzed_keys = set()
        for name in os.listdir(PHASE2_DIR):
            if not name.endswith(".json"):
                continue
            data = load_json_file(os.path.join(PHASE2_DIR, name))
            if data and isinstance(data, dict):
                for item in data.get("data", []):
                    key = item.get("url") or item.get("title", "")
                    if key:
                        analyzed_keys.add(key)
        logger.log(f"已分析记录数（去重前）: {len(analyzed_keys)}")

        # 加载最新 phase1 数据
        input_path = find_latest_file(PHASE1_DIR, prefix="phase1_", suffix=".json")
        if not input_path:
            raise FileNotFoundError("未找到 Phase1 数据文件")
        raw = load_json_file(input_path)
        items = raw.get("data", raw) if isinstance(raw, dict) else raw
        logger.log(f"Phase1 总记录数: {len(items)}")

        # 过滤出未分析的新增项
        new_items = [
            i for i in items
            if (i.get("url") or i.get("title", "")) not in analyzed_keys
        ]
        logger.log(f"新增待分析记录数: {len(new_items)}")

        if not new_items:
            logger.log("无新增数据需要分析")
            task.progress = 100
            task.result = {"total_analyzed": 0, "message": "无新增数据"}
            task.report = {"phase2": {"total_analyzed": 0, "summary": "无新增数据"}}
            task.status = "completed"
            task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _save_tasks_persist()
            return

        # 调用分析逻辑（复用 phase2 参数）
        inc_params = {**params, "input_file": input_path}
        if pipeline_v3 and hasattr(pipeline_v3, "run_phase2"):
            logger.log("调用 pipeline_v3.run_phase2() [增量模式]...")
            with StreamCapture(logger):
                result = pipeline_v3.run_phase2(
                    input_dir=PHASE1_DIR,
                    output_dir=PHASE2_DIR,
                    input_file=input_path,
                    items=new_items,
                    model=params.get("model"),
                    task=task,
                    incremental=True,
                )
            analyzed_items = result.get("items", []) if isinstance(result, dict) else []
            report_data = result.get("report", {}) if isinstance(result, dict) else {}
            output_file = result.get("output_file", "") if isinstance(result, dict) else ""
        else:
            # 回退到内置分析（仅处理 new_items）
            logger.log("pipeline_v3 不可用，使用内置增量分析...")
            # 临时构建一个子 task 用于复用 _run_phase2_task 的回退逻辑
            # 这里直接内联简化处理
            analyzed_items = []
            categories = {}
            total = len(new_items)
            for idx, item in enumerate(new_items):
                if task.stop_requested:
                    break
                title = item.get("title", "")
                content = item.get("content", "")
                category = "其他"
                for cat, keywords in {
                    "工程": ["工程", "施工", "建设"],
                    "货物": ["采购", "设备", "物资"],
                    "服务": ["服务", "咨询", "评估"],
                }.items():
                    if any(k in title for k in keywords):
                        category = cat
                        break
                categories[category] = categories.get(category, 0) + 1
                budget = None
                bm = re.search(r"(?:预算|控制价|金额)[^0-9]*([\d.]+)\s*万", content)
                if bm:
                    budget = float(bm.group(1))
                analyzed_items.append({
                    "title": title,
                    "url": item.get("url", ""),
                    "date": item.get("date", ""),
                    "category": category,
                    "budget": budget,
                    "snippet": content[:300] if content else "",
                })
                task.progress = int(90 * (idx + 1) / total)
                if (idx + 1) % 10 == 0:
                    logger.log(f"已分析 {idx + 1}/{total} 条")

            report_data = {
                "total_analyzed": len(analyzed_items),
                "categories": categories,
                "items": [{"title": a["title"], "category": a["category"]} for a in analyzed_items],
                "summary": f"增量分析 {len(analyzed_items)} 条新增公告",
            }
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(PHASE2_DIR, f"phase2_inc_{timestamp}.json")

        if task.stop_requested:
            task.status = "stopped"
            task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.log("任务已被用户停止", level="warning")
            _save_tasks_persist()
            return

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(PHASE2_DIR, f"phase2_inc_{timestamp}.json")

        save_json_file(output_file, {"data": analyzed_items, "report": report_data})
        logger.log(f"增量分析结果已保存: {output_file}")
        task.files.append(os.path.relpath(output_file, BASE_DIR))

        task.progress = 100
        task.result = {
            "output_file": os.path.relpath(output_file, BASE_DIR),
            "total_analyzed": len(analyzed_items),
            "incremental": True,
        }
        task.report = {"phase2": report_data}
        task.status = "completed"
        task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.log(f"增量分析任务完成! 新增分析 {len(analyzed_items)} 条")

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.log(f"增量分析任务失败: {e}", level="error")
        logger.log(traceback.format_exc(), level="error")

    _save_tasks_persist()


def _run_full_incremental_task(task: Task, params: dict):
    """执行增量完整流水线任务（增量采集 + 增量分析）。"""
    logger = task.logger
    logger.log("=" * 60)
    logger.log(f"开始执行增量完整流水线任务 (ID: {task.id})")
    logger.log("=" * 60)

    task.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task.status = "running"
    _save_tasks_persist()

    try:
        # ---- Phase1: 增量采集 ----
        logger.log(">>> 阶段 1/2: 增量数据采集")

        # 记录采集前的已有文件
        existing_files = set(os.listdir(PHASE1_DIR)) if os.path.exists(PHASE1_DIR) else set()

        _run_phase1_task(task, params)

        if task.status in ("failed", "stopped"):
            logger.log("增量采集未成功，终止流水线", level="warning")
            return

        # 找到新生成的 phase1 文件
        new_files = [f for f in os.listdir(PHASE1_DIR) if f not in existing_files]
        if not new_files and task.files:
            new_files = [os.path.basename(f) for f in task.files]

        phase1_output = task.files[-1] if task.files else None
        logger.log(f"新增 Phase1 文件: {new_files}")

        # ---- Phase2: 增量分析 ----
        logger.log(">>> 阶段 2/2: 增量智能分析")
        task.status = "running"
        task._stop_flag.clear()
        _save_tasks_persist()

        phase1_report = task.report.get("phase1", {}) if task.report else {}
        inc_params = {**params}
        if phase1_output:
            inc_params["input_file"] = phase1_output

        _run_phase2_incremental_task(task, inc_params)

        # 合并报告
        if task.report:
            phase2_report = task.report.get("phase2", {})
            task.report = {"phase1": phase1_report, "phase2": phase2_report}

        logger.log("增量完整流水线任务完成!")

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.log(f"增量完整流水线任务失败: {e}", level="error")
        logger.log(traceback.format_exc(), level="error")

    _save_tasks_persist()


# ===========================================================================
# 任务异步执行 & 停止
# ===========================================================================
_TASK_EXECUTORS = {
    "phase1": _run_phase1_task,
    "phase2": _run_phase2_task,
    "full": _run_full_task,
    "phase2_incremental": _run_phase2_incremental_task,
    "full_incremental": _run_full_incremental_task,
}

VALID_TASK_TYPES = list(_TASK_EXECUTORS.keys())


def _execute_task(task: Task):
    """任务执行入口，根据类型分派到对应执行器。"""
    executor = _TASK_EXECUTORS.get(task.type)
    if executor:
        try:
            executor(task, task.params)
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            task.logger.log(f"任务执行异常: {e}", level="error")
            task.logger.log(traceback.format_exc(), level="error")
            _save_tasks_persist()
    else:
        task.status = "failed"
        task.error = f"未知任务类型: {task.type}"
        task.logger.log(f"未知任务类型: {task.type}", level="error")
        _save_tasks_persist()


def run_task_async(task: Task):
    """在后台线程中异步执行任务。"""
    task._thread = threading.Thread(target=_execute_task, args=(task,), daemon=True)
    task._thread.start()


def stop_task(task_id: str) -> bool:
    """停止运行中的任务。"""
    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        return False
    if task.status != "running":
        return False
    task.request_stop()
    task.logger.log("收到停止请求，正在停止任务...", level="warning")
    task.status = "stopped"
    task.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save_tasks_persist()
    return True


# ===========================================================================
# 内置调度器（当 _scheduler 模块不可用时使用）
# ===========================================================================
class PipelineScheduler:
    """定时调度器，周期性执行流水线任务。"""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._interval = 3600          # 默认 1 小时
        self._enabled = False
        self._task_type = "full"
        self._params: dict = {}
        self._last_run: Optional[str] = None
        self._next_run: Optional[str] = None
        self._lock = threading.Lock()

    def start(self):
        """启动调度器线程。"""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("[SCHEDULER] 调度器已启动")

    def stop(self):
        """停止调度器线程。"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        print("[SCHEDULER] 调度器已停止")

    def _run_loop(self):
        """调度主循环。"""
        while not self._stop_event.is_set():
            with self._lock:
                enabled = self._enabled
                interval = self._interval
                task_type = self._task_type
                params = dict(self._params)

            if enabled:
                try:
                    task_id = str(uuid.uuid4())[:8]
                    task = Task(task_id, task_type, params)
                    task.logger.log("由定时调度器触发", level="info")
                    register_task(task)
                    run_task_async(task)
                    self._last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    next_dt = datetime.fromtimestamp(time.time() + interval)
                    self._next_run = next_dt.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[SCHEDULER] 触发任务 {task_id} ({task_type})")
                except Exception as e:
                    print(f"[SCHEDULER] 触发任务失败: {e}")

            # 等待间隔（可被 stop_event 中断）
            self._stop_event.wait(interval)

    def get_status(self) -> dict:
        """获取调度器状态。"""
        with self._lock:
            return {
                "enabled": self._enabled,
                "interval": self._interval,
                "task_type": self._task_type,
                "params": self._params,
                "last_run": self._last_run,
                "next_run": self._next_run,
                "running": self._thread is not None and self._thread.is_alive(),
            }

    def update(self, **kwargs):
        """更新调度器配置。"""
        with self._lock:
            if "enabled" in kwargs:
                self._enabled = kwargs["enabled"]
            if "interval" in kwargs:
                self._interval = max(60, int(kwargs["interval"]))
            if "task_type" in kwargs:
                if kwargs["task_type"] in VALID_TASK_TYPES:
                    self._task_type = kwargs["task_type"]
            if "params" in kwargs:
                self._params = kwargs["params"]
        # 持久化
        self._save_config()

    def toggle(self) -> bool:
        """切换调度器开关。"""
        with self._lock:
            self._enabled = not self._enabled
            state = self._enabled
        self._save_config()
        return state

    def trigger_now(self) -> Optional[str]:
        """立即触发一次调度任务。"""
        with self._lock:
            task_type = self._task_type
            params = dict(self._params)
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id, task_type, params)
        task.logger.log("由手动触发", level="info")
        register_task(task)
        run_task_async(task)
        self._last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return task_id

    def _save_config(self):
        """持久化调度器配置。"""
        with self._lock:
            config = {
                "enabled": self._enabled,
                "interval": self._interval,
                "task_type": self._task_type,
                "params": self._params,
            }
        save_json_file(SCHEDULER_CONFIG_FILE, config)

    def load_config(self):
        """从文件加载调度器配置。"""
        config = load_json_file(SCHEDULER_CONFIG_FILE)
        if config and isinstance(config, dict):
            with self._lock:
                self._enabled = config.get("enabled", False)
                self._interval = max(60, config.get("interval", 3600))
                self._task_type = config.get("task_type", "full")
                self._params = config.get("params", {})
            print(f"[SCHEDULER] 已加载配置: enabled={self._enabled}, interval={self._interval}s, type={self._task_type}")


# 全局调度器实例
scheduler_instance = PipelineScheduler()


# ===========================================================================
# 系统辅助函数
# ===========================================================================
def check_health() -> dict:
    """系统健康检查。"""
    components = {
        "pipeline_v3": pipeline_v3 is not None,
        "config": _config is not None,
        "scheduler": _scheduler is not None or scheduler_instance is not None,
        "search": _search is not None,
        "merge": _merge is not None,
        "history": _history is not None,
    }
    directories = {
        "data": os.path.exists(DATA_DIR),
        "phase1": os.path.exists(PHASE1_DIR),
        "phase2": os.path.exists(PHASE2_DIR),
        "uploads": os.path.exists(UPLOAD_DIR),
    }
    with _TASKS_LOCK:
        task_count = len(TASKS)
        running_count = len([t for t in TASKS.values() if t.status == "running"])

    all_ok = all(components.values()) and all(directories.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "components": components,
        "directories": directories,
        "tasks": {"total": task_count, "running": running_count},
        "scheduler": scheduler_instance.get_status(),
    }


def get_stats() -> dict:
    """获取全局统计数据。"""
    with _TASKS_LOCK:
        tasks = list(TASKS.values())

    stats = {
        "total_tasks": len(tasks),
        "running": len([t for t in tasks if t.status == "running"]),
        "completed": len([t for t in tasks if t.status == "completed"]),
        "failed": len([t for t in tasks if t.status == "failed"]),
        "stopped": len([t for t in tasks if t.status == "stopped"]),
        "pending": len([t for t in tasks if t.status == "pending"]),
        "by_type": {},
        "total_collected": 0,
        "total_analyzed": 0,
        "files": {
            "phase1": len([f for f in os.listdir(PHASE1_DIR) if os.path.isfile(os.path.join(PHASE1_DIR, f))]) if os.path.exists(PHASE1_DIR) else 0,
            "phase2": len([f for f in os.listdir(PHASE2_DIR) if os.path.isfile(os.path.join(PHASE2_DIR, f))]) if os.path.exists(PHASE2_DIR) else 0,
            "uploads": len([f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]) if os.path.exists(UPLOAD_DIR) else 0,
        },
    }

    for t in tasks:
        stats["by_type"][t.type] = stats["by_type"].get(t.type, 0) + 1
        if t.report and isinstance(t.report, dict):
            p1 = t.report.get("phase1", t.report.get("phase1_report", {}))
            if isinstance(p1, dict):
                stats["total_collected"] += p1.get("total", p1.get("total_collected", 0))
            p2 = t.report.get("phase2", t.report.get("phase2_report", {}))
            if isinstance(p2, dict):
                stats["total_analyzed"] += p2.get("total_analyzed", p2.get("total", 0))

    return stats


def get_sanitized_config() -> dict:
    """获取脱敏后的配置信息。"""
    if _config:
        raw = _config.load_config()
        # 脱敏
        for key in list(raw.keys()):
            if any(s in key.upper() for s in ("KEY", "SECRET", "PASSWORD", "TOKEN")):
                val = str(raw[key])
                raw[key] = val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
        return raw
    return {
        "status": "config module not loaded",
        "data_dir": DATA_DIR,
        "phase1_dir": PHASE1_DIR,
        "phase2_dir": PHASE2_DIR,
        "upload_dir": UPLOAD_DIR,
    }


def get_history() -> list:
    """获取任务历史。"""
    if _history and hasattr(_history, "get_history"):
        try:
            return _history.get_history()
        except Exception:
            pass
    # 回退：从 TASKS 构建简要历史
    with _TASKS_LOCK:
        tasks = sorted(TASKS.values(), key=lambda t: t.created_at, reverse=True)
    return [
        {
            "id": t.id,
            "type": t.type,
            "status": t.status,
            "created_at": t.created_at,
            "finished_at": t.finished_at,
            "summary": build_report(t).get("summary", ""),
        }
        for t in tasks[:50]
    ]


# ===========================================================================
# FastAPI 应用
# ===========================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时加载历史任务和调度器，关闭时保存状态。"""
    # ---- 启动 ----
    print("[STARTUP] 加载历史任务...")
    _load_tasks_persist()

    print("[STARTUP] 加载调度器配置...")
    scheduler_instance.load_config()
    scheduler_instance.start()

    print("[STARTUP] 招标公告采集与处理流水线服务已启动")
    yield
    # ---- 关闭 ----
    print("[SHUTDOWN] 停止调度器...")
    scheduler_instance.stop()

    print("[SHUTDOWN] 保存任务状态...")
    _save_tasks_persist()

    print("[SHUTDOWN] 服务已关闭")


app = FastAPI(
    title="招标公告采集与处理流水线",
    description="基于 FastAPI 的招标公告采集、智能分析与流水线管理后台",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件目录
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="frontend_static")


# ===========================================================================
# 路由
# ===========================================================================

# ---- 首页 ----
@app.get("/")
async def index():
    """提供前端 index.html。"""
    index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        {"message": "前端文件未找到，请确保 frontend/index.html 存在"},
        status_code=404,
    )


# ---- 任务管理 ----
@app.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="按状态过滤: pending/running/completed/failed/stopped"),
    task_type: Optional[str] = Query(None, description="按类型过滤"),
    limit: int = Query(100, ge=1, le=500, description="返回数量上限"),
):
    """获取任务列表。"""
    with _TASKS_LOCK:
        tasks = list(TASKS.values())

    if status:
        tasks = [t for t in tasks if t.status == status]
    if task_type:
        tasks = [t for t in tasks if t.type == task_type]

    tasks.sort(key=lambda t: t.created_at, reverse=True)
    tasks = tasks[:limit]

    return {
        "total": len(TASKS),
        "filtered": len(tasks),
        "tasks": [t.to_dict() for t in tasks],
    }


@app.post("/api/tasks/{task_type}")
async def create_task(task_type: str, params: dict = Body(default={})):
    """创建并启动一个新任务。"""
    if task_type not in VALID_TASK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的任务类型: {task_type}，有效类型: {VALID_TASK_TYPES}",
        )

    task_id = str(uuid.uuid4())[:8]
    task = Task(task_id, task_type, params)
    task.logger.log(f"任务已创建 (类型: {task_type})")
    register_task(task)
    run_task_async(task)

    return {
        "task_id": task_id,
        "type": task_type,
        "status": task.status,
        "message": "任务已创建并开始执行",
    }


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """获取任务详情。"""
    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    return task.to_dict()


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务。"""
    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    if task.status == "running":
        raise HTTPException(status_code=400, detail="无法删除运行中的任务，请先停止")

    with _TASKS_LOCK:
        del TASKS[task_id]
    _save_tasks_persist()

    return {"message": f"任务 {task_id} 已删除"}


@app.post("/api/tasks/{task_id}/stop")
async def stop_task_route(task_id: str):
    """停止运行中的任务。"""
    success = stop_task(task_id)
    if not success:
        with _TASKS_LOCK:
            task = TASKS.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        raise HTTPException(status_code=400, detail=f"任务状态为 {task.status}，无法停止")
    return {"message": f"任务 {task_id} 停止请求已发送"}


@app.get("/api/tasks/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    after: int = Query(0, ge=0, description="从第几条日志开始获取"),
    since_idx: int = Query(None, ge=0, description="兼容前端: 同 after"),
    level: Optional[str] = Query(None, description="按级别过滤: info/warning/error"),
):
    """获取任务日志。"""
    # 兼容前端使用的 since_idx 参数
    effective_after = since_idx if since_idx is not None else after
    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    logs = task.logger.get_logs(effective_after)
    if level:
        logs = [l for l in logs if l["level"] == level]

    return {
        "task_id": task_id,
        "total_logs": task.logger.count,
        "returned": len(logs),
        "logs": logs,
        "next_idx": task.logger.count,
        "task_status": task.status,
    }


@app.get("/api/tasks/{task_id}/logs/download")
async def download_task_logs(task_id: str):
    """下载任务日志文件。"""
    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    log_text = task.logger.get_log_text()
    filename = f"task_{task_id}_logs.txt"
    return PlainTextResponse(
        content=log_text,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/tasks/{task_id}/report")
async def get_task_report(task_id: str):
    """获取任务报告。"""
    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    report = build_report(task)
    return report


@app.get("/api/tasks/{task_id}/files")
async def get_task_files(task_id: str):
    """获取任务输出文件列表。"""
    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    files = []
    for rel_path in task.files:
        full_path = os.path.join(BASE_DIR, rel_path)
        if os.path.exists(full_path):
            stat = os.stat(full_path)
            files.append({
                "name": os.path.basename(rel_path),
                "path": rel_path,
                "size": stat.st_size,
                "size_human": _human_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })

    return {"task_id": task_id, "files": files}


@app.get("/api/tasks/{task_id}/download")
async def download_task_result(task_id: str):
    """下载任务结果文件（最新的输出文件）。"""
    with _TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    if not task.files:
        raise HTTPException(status_code=404, detail="任务没有输出文件")

    # 下载最新的文件
    rel_path = task.files[-1]
    full_path = os.path.join(BASE_DIR, rel_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {rel_path}")

    return FileResponse(
        full_path,
        media_type="application/json",
        filename=os.path.basename(rel_path),
    )


# ---- 文件管理 ----
@app.get("/api/files")
async def list_all_files(
    category: Optional[str] = Query(None, description="分类过滤: phase1/phase2/uploads"),
):
    """列出所有数据文件。"""
    all_files = []
    categories = ["phase1", "phase2", "uploads"] if not category else [category]

    for cat in categories:
        cat_dir = get_category_dir(cat)
        if cat_dir:
            all_files.extend(list_files(cat_dir, cat))

    return {
        "total": len(all_files),
        "files": all_files,
    }


@app.get("/api/files/{category}/{filename:path}")
async def download_file(category: str, filename: str):
    """下载指定文件。"""
    cat_dir = get_category_dir(category)
    if not cat_dir:
        raise HTTPException(status_code=400, detail=f"无效的分类: {category}")

    # 防止路径遍历
    safe_name = os.path.basename(filename)
    file_path = os.path.join(cat_dir, safe_name)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    return FileResponse(file_path, filename=safe_name)


@app.delete("/api/files/{category}/{filename:path}")
async def delete_file(category: str, filename: str):
    """删除指定文件。"""
    cat_dir = get_category_dir(category)
    if not cat_dir:
        raise HTTPException(status_code=400, detail=f"无效的分类: {category}")

    safe_name = os.path.basename(filename)
    file_path = os.path.join(cat_dir, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    os.remove(file_path)
    return {"message": f"文件 {safe_name} 已删除"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件到 uploads 目录。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件")

    safe_name = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "filename": safe_name,
        "size": len(content),
        "size_human": _human_size(len(content)),
        "path": os.path.relpath(file_path, BASE_DIR),
        "message": "文件上传成功",
    }


# ---- 搜索 ----
@app.get("/api/search")
async def search(
    q: str = Query(..., description="搜索关键词"),
    category: str = Query("all", description="搜索范围: all/phase1/phase2"),
    limit: int = Query(50, ge=1, le=500),
):
    """搜索采集和分析的数据。"""
    if _search and hasattr(_search, "search"):
        try:
            results = _search.search(q, category=category, limit=limit)
            return {"query": q, "results": results, "total": len(results)}
        except Exception:
            pass

    # 回退：内置搜索
    results = []
    search_dirs = []
    if category in ("all", "phase1"):
        search_dirs.append(("phase1", PHASE1_DIR))
    if category in ("all", "phase2"):
        search_dirs.append(("phase2", PHASE2_DIR))

    for cat, directory in search_dirs:
        if not os.path.exists(directory):
            continue
        for name in os.listdir(directory):
            if not name.endswith(".json"):
                continue
            filepath = os.path.join(directory, name)
            data = load_json_file(filepath)
            if not data:
                continue
            items = data.get("data", data) if isinstance(data, dict) else data
            if not isinstance(items, list):
                continue
            for item in items:
                title = item.get("title", "")
                content = item.get("content", item.get("snippet", ""))
                if q.lower() in title.lower() or q.lower() in str(content).lower():
                    results.append({
                        "category": cat,
                        "file": name,
                        "title": title,
                        "url": item.get("url", ""),
                        "date": item.get("date", ""),
                        "snippet": str(content)[:200] if content else "",
                        "budget": item.get("budget"),
                        "deadline": item.get("deadline"),
                    })
                    if len(results) >= limit:
                        break
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    return {"query": q, "results": results, "total": len(results)}


# ---- 合并 ----
@app.post("/api/merge")
async def merge_results(body: dict = Body(default={})):
    """合并多个采集结果文件。"""
    files = body.get("files", [])
    output_name = body.get("output_name", f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    if _merge and hasattr(_merge, "merge_results"):
        try:
            result = _merge.merge_results(files, os.path.join(PHASE1_DIR, output_name))
            return result
        except Exception:
            pass

    # 回退：内置合并
    all_items = []
    for filepath in files:
        full_path = filepath if os.path.isabs(filepath) else os.path.join(BASE_DIR, filepath)
        if not os.path.exists(full_path):
            full_path = os.path.join(PHASE1_DIR, os.path.basename(filepath))
        if not os.path.exists(full_path):
            continue
        data = load_json_file(full_path)
        if not data:
            continue
        items = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(items, list):
            all_items.extend(items)

    output_path = os.path.join(PHASE1_DIR, output_name)
    save_json_file(output_path, {"data": all_items, "merged_from": files, "merged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    return {
        "output_file": output_name,
        "total": len(all_items),
        "merged_from": files,
        "path": os.path.relpath(output_path, BASE_DIR),
    }


# ---- 调度器管理 ----
@app.get("/api/scheduler")
async def get_scheduler_status():
    """获取调度器状态。"""
    return scheduler_instance.get_status()


@app.put("/api/scheduler")
async def update_scheduler(body: dict = Body(...)):
    """更新调度器配置。"""
    scheduler_instance.update(**body)
    return {
        "message": "调度器配置已更新",
        "status": scheduler_instance.get_status(),
    }


@app.post("/api/scheduler/toggle")
async def toggle_scheduler():
    """切换调度器开关。"""
    enabled = scheduler_instance.toggle()
    return {
        "enabled": enabled,
        "message": f"调度器已{'启用' if enabled else '禁用'}",
    }


@app.post("/api/scheduler/run")
async def trigger_scheduler_run():
    """立即触发一次调度任务。"""
    task_id = scheduler_instance.trigger_now()
    return {
        "task_id": task_id,
        "message": "调度任务已触发",
    }


# ---- 系统信息 ----
@app.get("/api/health")
async def health_check():
    """健康检查。"""
    if _health and hasattr(_health, "check"):
        try:
            return _health.check()
        except Exception:
            pass
    return check_health()


@app.get("/api/stats")
async def get_statistics():
    """获取全局统计数据。"""
    return get_stats()


@app.get("/api/config")
async def get_config():
    """获取配置信息（脱敏）。"""
    return get_sanitized_config()


@app.get("/api/history")
async def get_task_history():
    """获取任务历史。"""
    return {"history": get_history()}


@app.get("/api/phases")
async def get_phase_info():
    """获取流水线阶段信息。"""
    return {
        "phases": [
            {
                "id": "phase1",
                "name": "数据采集",
                "description": "从各数据源采集招标公告",
                "output_dir": PHASE1_DIR,
            },
            {
                "id": "phase2",
                "name": "智能分析",
                "description": "使用 AI 分析采集到的公告",
                "output_dir": PHASE2_DIR,
            },
        ],
        "task_types": [
            {"id": "phase1", "name": "Phase1 采集", "description": "仅执行数据采集"},
            {"id": "phase2", "name": "Phase2 分析", "description": "仅执行智能分析"},
            {"id": "full", "name": "完整流水线", "description": "依次执行采集和分析"},
            {"id": "phase2_incremental", "name": "增量分析", "description": "仅分析新增数据"},
            {"id": "full_incremental", "name": "增量流水线", "description": "增量采集并分析"},
        ],
        "directories": {
            "base": BASE_DIR,
            "data": DATA_DIR,
            "phase1": PHASE1_DIR,
            "phase2": PHASE2_DIR,
            "uploads": UPLOAD_DIR,
        },
    }


# ===========================================================================
# 进程退出钩子
# ===========================================================================
def _on_shutdown():
    """进程退出时的清理函数。"""
    print("[ATEXIT] 保存任务状态...")
    _save_tasks_persist()
    scheduler_instance.stop()
    print("[ATEXIT] 清理完成")


atexit.register(_on_shutdown)


def _signal_handler(signum, frame):
    """信号处理函数。"""
    print(f"\n[SIGNAL] 收到信号 {signum}，正在关闭...")
    _on_shutdown()
    sys.exit(0)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ===========================================================================
# 前端兼容路由（匹配 Vue 前端期望的 API 路径）
# ===========================================================================

@app.get("/api/files/phase1")
async def compat_list_phase1_files():
    """列出 Phase 1 采集文件（JSON）"""
    files = list_files(PHASE1_DIR, "phase1") if os.path.exists(PHASE1_DIR) else []
    return {"files": files}


@app.get("/api/files/phase2")
async def compat_list_phase2_files():
    """列出 Phase 2 处理文件（Excel），带记录数"""
    if _history and hasattr(_history, "list_phase2_files"):
        return {"files": _history.list_phase2_files()}
    files = list_files(PHASE2_DIR, "phase2") if os.path.exists(PHASE2_DIR) else []
    return {"files": files}


@app.post("/api/files/phase1/upload")
async def compat_upload_phase1(file: UploadFile = File(...)):
    """上传 JSON 文件到 Phase 1 目录"""
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="仅允许 .json 文件")
    safe_name = os.path.basename(file.filename)
    content = await file.read()
    with open(os.path.join(PHASE1_DIR, safe_name), "wb") as f:
        f.write(content)
    return {"ok": True, "name": safe_name}


@app.post("/api/files/phase2/upload")
async def compat_upload_phase2(file: UploadFile = File(...)):
    """上传 Excel 文件到 Phase 2 目录"""
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅允许 .xlsx 文件")
    safe_name = os.path.basename(file.filename)
    content = await file.read()
    with open(os.path.join(PHASE2_DIR, safe_name), "wb") as f:
        f.write(content)
    return {"ok": True, "name": safe_name}


@app.get("/api/files/phase1/{filename:path}/preview")
async def compat_preview_phase1(filename: str):
    """预览 Phase 1 JSON 文件（前20条）"""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(PHASE1_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        preview = []
        for item in data[:20]:
            preview.append({
                "title": item.get("title", "")[:80],
                "date": item.get("date", ""),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                "has_content": bool(item.get("content", "")),
            })
        return {"total": len(data), "preview": preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def compat_search(body: dict = Body(...)):
    """关键词搜索（POST 方式，匹配前端调用）"""
    keyword = body.get("keyword", "").strip()
    fields = body.get("fields")
    match_mode = body.get("match_mode", "any")
    if not keyword:
        return {"total": 0, "results": [], "scanned_files": 0, "error": "关键词为空"}
    if _search and hasattr(_search, "search"):
        try:
            result = _search.search(keyword, fields=fields, match_mode=match_mode)
            if hasattr(_search, "format_search_text"):
                result["text"] = _search.format_search_text(result)
            return result
        except Exception as e:
            return {"total": 0, "results": [], "error": str(e)}
    return {"total": 0, "results": [], "error": "搜索模块未加载"}


@app.post("/api/config")
async def compat_save_config(body: dict = Body(...)):
    """保存配置"""
    if not _config:
        raise HTTPException(status_code=500, detail="配置模块未加载")
    cfg = _config.load_config()
    if "sim_threshold" in body:
        try:
            val = float(body["sim_threshold"])
            if 0 <= val <= 1:
                cfg["sim_threshold"] = val
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="阈值必须是 0~1 之间的数字")
    if "schedule_enabled" in body:
        cfg["schedule_enabled"] = bool(body["schedule_enabled"])
    if "ai_verify" in body:
        cfg["ai_verify"] = bool(body["ai_verify"])
    _config.save_config(cfg)
    return {"ok": True, "config": cfg}


@app.get("/api/schedules")
async def compat_list_schedules():
    """列出定时任务"""
    if _scheduler and hasattr(_scheduler, "list_schedules"):
        return {"schedules": _scheduler.list_schedules()}
    return {"schedules": []}


@app.post("/api/schedules")
async def compat_add_schedule(body: dict = Body(...)):
    """添加定时任务"""
    if not _scheduler:
        raise HTTPException(status_code=500, detail="调度器模块未加载")
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="必须填写任务名称")
    task_type = body.get("task_type", "full")
    schedule_type = body.get("schedule_type", "once")
    run_time = body.get("run_time", "").strip()
    if not run_time:
        raise HTTPException(status_code=400, detail="必须填写执行时间")
    weekday = body.get("weekday")
    try:
        sched = _scheduler.add_schedule(
            name=name,
            task_type=task_type,
            schedule_type=schedule_type,
            run_time=run_time,
            weekday=weekday,
            incremental=body.get("incremental", False),
            params=body.get("params", {}),
        )
        return {"ok": True, "schedule": sched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/schedules/{sid}")
async def compat_delete_schedule(sid: str):
    """删除定时任务"""
    if not _scheduler:
        raise HTTPException(status_code=500, detail="调度器模块未加载")
    if _scheduler.delete_schedule(sid):
        return {"ok": True}
    raise HTTPException(status_code=404, detail="调度项不存在")


@app.post("/api/schedules/{sid}/toggle")
async def compat_toggle_schedule(sid: str, body: dict = Body(...)):
    """启用/禁用定时任务"""
    if not _scheduler:
        raise HTTPException(status_code=500, detail="调度器模块未加载")
    enabled = body.get("enabled", True)
    sched = _scheduler.toggle_schedule(sid, enabled)
    if sched:
        return {"ok": True, "schedule": sched}
    raise HTTPException(status_code=404, detail="调度项不存在")


@app.post("/api/schedules/{sid}/run")
async def compat_run_schedule(sid: str):
    """立即运行定时任务"""
    # 找到该 schedule 并触发一次 full 任务
    if not _scheduler:
        raise HTTPException(status_code=500, detail="调度器模块未加载")
    for s in _scheduler.list_schedules():
        if s["id"] == sid:
            task_type = s.get("task_type", "full")
            if s.get("incremental") and task_type == "full":
                task_type = "full_incremental"
            task = register_task(task_type, s.get("params", {}))
            run_task_async(task)
            return {"ok": True, "task_id": task.task_id}
    raise HTTPException(status_code=404, detail="调度项不存在")


@app.get("/api/history/files")
async def compat_history_files():
    """列出 Phase 2 历史文件（含记录数）"""
    if _history and hasattr(_history, "list_phase2_files"):
        return {"files": _history.list_phase2_files()}
    return {"files": []}


@app.get("/api/history/stats")
async def compat_history_stats():
    """全量已处理记录统计"""
    if _history:
        keys = _history.collect_all_processed_keys() if hasattr(_history, "collect_all_processed_keys") else set()
        files = _history.list_phase2_files() if hasattr(_history, "list_phase2_files") else []
        return {"total_processed": len(keys), "file_count": len(files), "files": files}
    return {"total_processed": 0, "file_count": 0, "files": []}


@app.post("/api/merge/by-files")
async def compat_merge_by_files(body: dict = Body(...)):
    """按选中文件合并"""
    if not _merge:
        raise HTTPException(status_code=500, detail="合并模块未加载")
    files = body.get("files", [])
    if not files:
        raise HTTPException(status_code=400, detail="必须选择至少一个文件")
    try:
        output_path = _merge.merge_files(files)
        output_name = os.path.basename(output_path)
        return {"ok": True, "output_file": output_name, "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/merge/by-time")
async def compat_merge_by_time(body: dict = Body(...)):
    """按时间范围合并"""
    if not _merge:
        raise HTTPException(status_code=500, detail="合并模块未加载")
    start_date = body.get("start_date", "").strip()
    end_date = body.get("end_date", "").strip()
    if not start_date or not end_date:
        raise HTTPException(status_code=400, detail="必须指定起止日期")
    try:
        output_path = _merge.merge_by_time(start_date, end_date)
        if not output_path:
            raise HTTPException(status_code=404, detail="该时间范围内无文件")
        output_name = os.path.basename(output_path)
        return {"ok": True, "output_file": output_name, "path": output_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health/sources")
async def compat_health_sources():
    """采集来源健康检查"""
    if _health and hasattr(_health, "check_all_sources"):
        try:
            return _health.check_all_sources()
        except Exception as e:
            return {"error": str(e)}
    return {"error": "健康检查模块未加载"}


@app.post("/api/files/phase2/process")
async def compat_process_phase2(body: dict = Body(...)):
    """对指定 Phase 1 文件执行 Phase 2 处理"""
    input_file = body.get("input_file", "")
    if not input_file:
        raise HTTPException(status_code=400, detail="必须指定 input_file")
    if not os.path.isabs(input_file):
        input_file = os.path.join(BASE_DIR, input_file)
    task = register_task("phase2", {"input_file": input_file})
    run_task_async(task)
    return {"task_id": task.task_id, "status": task.status}


# ===========================================================================
# 启动入口
# ===========================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8200,
        reload=True,
    )
