# -*- coding: utf-8 -*-
"""
持久化配置存储 - 管理客户匹配阈值等可配置参数。
配置文件保存在 data/config.json。
"""
import os
import json
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

_lock = threading.Lock()

# 默认配置
_DEFAULTS = {
    "sim_threshold": 0.70,       # 客户匹配相似度阈值（SequenceMatcher.ratio，越大越严）
    "schedule_enabled": True,    # 定时任务总开关
    "ai_verify": True,           # 客户匹配后用 AI 模型再核对一次（默认开启）
}


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> dict:
    """读取配置，缺失字段用默认值补全"""
    _ensure_dir()
    if not os.path.exists(CONFIG_FILE):
        save_config(_DEFAULTS)
        return dict(_DEFAULTS)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # 补全缺失字段
        for k, v in _DEFAULTS.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    except Exception:
        return dict(_DEFAULTS)


def save_config(cfg: dict) -> None:
    """保存配置到文件"""
    _ensure_dir()
    with _lock:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)


def get(key: str, default=None):
    """读取单个配置项"""
    cfg = load_config()
    return cfg.get(key, default)


def set(key: str, value) -> None:
    """设置单个配置项并保存"""
    with _lock:
        cfg = load_config()
        cfg[key] = value
        save_config(cfg)


def get_threshold() -> float:
    """获取客户匹配阈值"""
    # 与 _DEFAULTS["sim_threshold"] 保持一致：0.70
    return float(get("sim_threshold", 0.70))


def set_threshold(threshold: float) -> None:
    """设置客户匹配阈值"""
    set("sim_threshold", float(threshold))
