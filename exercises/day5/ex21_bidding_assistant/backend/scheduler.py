# -*- coding: utf-8 -*-
"""
定时任务调度器 - 支持单次、每日、每周定时执行采集任务。
调度配置持久化保存在 data/schedules.json。
调度器在后台线程中运行，每分钟检查一次到期任务。
"""
import os
import json
import uuid
import threading
import time
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULE_FILE = os.path.join(BASE_DIR, "data", "schedules.json")

_lock = threading.RLock()       # 用可重入锁，允许 add/update 内部调 save
_schedules: list = []          # 调度列表
_scheduler_thread = None
_scheduler_stop = threading.Event()
_on_trigger = None             # 回调：当任务到期时调用 on_trigger(schedule)


def _ensure_dir():
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)


def load_schedules() -> list:
    """从文件加载调度列表"""
    global _schedules
    _ensure_dir()
    if not os.path.exists(SCHEDULE_FILE):
        _schedules = []
        return _schedules
    try:
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            _schedules = json.load(f)
    except Exception:
        _schedules = []
    return _schedules


def save_schedules() -> None:
    """保存调度列表到文件"""
    _ensure_dir()
    with _lock:
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(_schedules, f, ensure_ascii=False, indent=2)


def add_schedule(name: str, task_type: str, schedule_type: str,
                 run_time: str, weekday: int = None,
                 incremental: bool = False, params: dict = None) -> dict:
    """
    添加一个定时任务。
    name:           任务名称
    task_type:      任务类型 (phase1 / phase2 / full)
    schedule_type:  调度类型 (once / daily / weekly)
    run_time:       执行时间
                     - once:   "YYYY-MM-DD HH:MM"
                     - daily:  "HH:MM"
                     - weekly: "HH:MM"（配合 weekday）
    weekday:        周几执行（0=周一 ... 6=周日），仅 weekly 模式
    incremental:    是否启用增量去重（phase2/full 时有效）
    params:         附加参数（如 input_file）
    返回：创建的调度项
    """
    sched = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "task_type": task_type,
        "schedule_type": schedule_type,
        "run_time": run_time,
        "weekday": weekday,
        "incremental": incremental,
        "params": params or {},
        "enabled": True,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_run": None,
        "last_run_task_id": None,
        "next_run": _calc_next_run(schedule_type, run_time, weekday),
    }
    with _lock:
        _schedules.append(sched)
        save_schedules()
    return sched


def update_schedule(sid: str, updates: dict) -> dict:
    """更新调度项"""
    with _lock:
        for s in _schedules:
            if s["id"] == sid:
                s.update(updates)
                # 重新计算下次运行时间
                if "schedule_type" in updates or "run_time" in updates or "weekday" in updates:
                    s["next_run"] = _calc_next_run(
                        s["schedule_type"], s["run_time"], s.get("weekday"))
                save_schedules()
                return s
    return None


def delete_schedule(sid: str) -> bool:
    """删除调度项"""
    with _lock:
        for i, s in enumerate(_schedules):
            if s["id"] == sid:
                _schedules.pop(i)
                save_schedules()
                return True
    return False


def toggle_schedule(sid: str, enabled: bool) -> dict:
    """启用/禁用调度项"""
    return update_schedule(sid, {"enabled": enabled})


def list_schedules() -> list:
    """返回所有调度项"""
    return list(_schedules)


def _calc_next_run(schedule_type: str, run_time: str, weekday: int = None) -> str:
    """计算下次运行时间，返回 "YYYY-MM-DD HH:MM" 字符串"""
    now = datetime.now()
    if schedule_type == "once":
        try:
            target = datetime.strptime(run_time, "%Y-%m-%d %H:%M")
            if target <= now:
                return None  # 已过期
            return target.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return None
    elif schedule_type == "daily":
        try:
            t = datetime.strptime(run_time, "%H:%M").time()
            target = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return None
    elif schedule_type == "weekly":
        try:
            t = datetime.strptime(run_time, "%H:%M").time()
            target = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            days_ahead = (weekday - target.weekday()) % 7
            target += timedelta(days=days_ahead)
            if target <= now:
                target += timedelta(weeks=1)
            return target.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return None
    return None


def _check_and_trigger():
    """检查是否有到期任务，有则触发回调"""
    now = datetime.now()
    with _lock:
        due = []
        for s in _schedules:
            if not s.get("enabled", True):
                continue
            next_run = s.get("next_run")
            if not next_run:
                continue
            try:
                target = datetime.strptime(next_run, "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if target <= now:
                due.append(s)

    for s in due:
        if _on_trigger:
            try:
                task_id = _on_trigger(s)
                s["last_run"] = now.strftime("%Y-%m-%d %H:%M:%S")
                s["last_run_task_id"] = task_id
            except Exception as e:
                print(f"[scheduler] 触发任务失败 {s['name']}: {e}")
        # 更新下次运行时间
        new_next = _calc_next_run(
            s["schedule_type"], s["run_time"], s.get("weekday"))
        s["next_run"] = new_next
        # 单次任务执行后自动禁用
        if s["schedule_type"] == "once":
            s["enabled"] = False

    if due:
        save_schedules()


def _scheduler_loop():
    """调度器主循环，每 10 秒检查一次"""
    # 启动时立即检查一次，避免错过启动时刻已到期的任务
    try:
        _check_and_trigger()
    except Exception as e:
        print(f"[scheduler] 启动检查异常: {e}")
    while not _scheduler_stop.is_set():
        try:
            _check_and_trigger()
        except Exception as e:
            print(f"[scheduler] 检查异常: {e}")
        _scheduler_stop.wait(10)


def start_scheduler(on_trigger_callback):
    """启动调度器后台线程。on_trigger_callback(schedule) -> task_id"""
    global _scheduler_thread, _on_trigger
    load_schedules()
    _on_trigger = on_trigger_callback
    _scheduler_stop.clear()
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()
    print("[scheduler] 定时调度器已启动")


def stop_scheduler():
    """停止调度器"""
    _scheduler_stop.set()
    if _scheduler_thread:
        _scheduler_thread.join(timeout=5)
    print("[scheduler] 定时调度器已停止")
