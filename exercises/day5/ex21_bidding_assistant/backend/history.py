# -*- coding: utf-8 -*-
"""
历史记录管理 - 读取已生成的 phase2 Excel 文件，提取已处理的招标公告
用于增量去重：在 phase2 模型提取前，去掉已经提取过的公告。

去重键：(title, date) 二元组，与 pipeline_v3.dedup 保持一致。
"""
import os
import re
import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHASE2_DIR = os.path.join(BASE_DIR, "data", "phase2")


def _normalize_date(date_str: str) -> str:
    """统一日期格式为 YYYY-MM-DD"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', str(date_str) or "")
    return match.group(1) if match else str(date_str or "").strip()


def _make_key(title: str, date: str) -> tuple:
    """构造去重键"""
    return (str(title or "").strip(), _normalize_date(date))


def read_excel_keys(xlsx_path: str) -> set:
    """
    读取单个 phase2 Excel 文件，返回已处理公告的 (title, date) 集合。
    Excel 列顺序参考 pipeline_v3._COLUMNS：
      A=公告标题, B=招标人, C=发布日期, D=开标日期, E=预算金额,
      F=信息化, G=公告期限, H=数据来源, I=是否所属客户, J=公告链接
    """
    keys = set()
    if not os.path.exists(xlsx_path):
        return keys
    try:
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        ws = wb.active
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row:
                continue
            title = row[0] if len(row) > 0 else ""
            date = row[2] if len(row) > 2 else ""
            if title and str(title).strip():
                keys.add(_make_key(title, date))
        wb.close()
    except Exception as e:
        print(f"[history] 读取 Excel 失败 {xlsx_path}: {e}")
    return keys


def collect_processed_keys(xlsx_files: list) -> set:
    """
    从多个 phase2 Excel 文件中收集所有已处理的 (title, date) 键。
    xlsx_files: 文件名列表（不含路径，位于 PHASE2_DIR 下）或完整路径列表。
    """
    all_keys = set()
    for f in xlsx_files:
        path = f if os.path.isabs(f) else os.path.join(PHASE2_DIR, f)
        keys = read_excel_keys(path)
        all_keys.update(keys)
        print(f"[history] {os.path.basename(path)}: 已处理 {len(keys)} 条")
    return all_keys


def collect_all_processed_keys() -> set:
    """读取 PHASE2_DIR 下所有 Excel 文件，收集全部已处理记录"""
    all_keys = set()
    if not os.path.exists(PHASE2_DIR):
        return all_keys
    xlsx_files = [f for f in os.listdir(PHASE2_DIR) if f.lower().endswith(".xlsx")]
    all_keys = collect_processed_keys(xlsx_files)
    print(f"[history] 全量已处理记录: {len(all_keys)} 条（来自 {len(xlsx_files)} 个文件）")
    return all_keys


def filter_unprocessed(records: list, processed_keys: set) -> tuple:
    """
    从采集记录列表中过滤掉已处理的公告。
    返回：(未处理记录列表, 被过滤数量)
    """
    unprocessed = []
    skipped = 0
    for item in records:
        key = _make_key(item.get("title", ""), item.get("date", ""))
        if key in processed_keys:
            skipped += 1
        else:
            unprocessed.append(item)
    return unprocessed, skipped


def list_phase2_files() -> list:
    """列出所有 phase2 Excel 文件，按修改时间倒序"""
    if not os.path.exists(PHASE2_DIR):
        return []
    from datetime import datetime
    items = []
    for name in os.listdir(PHASE2_DIR):
        if not name.lower().endswith(".xlsx"):
            continue
        full = os.path.join(PHASE2_DIR, name)
        if not os.path.isfile(full):
            continue
        stat = os.stat(full)
        items.append({
            "name": name,
            "size_kb": round(stat.st_size / 1024, 1),
            "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "record_count": len(read_excel_keys(full)),
        })
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items
