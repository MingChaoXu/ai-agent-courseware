# -*- coding: utf-8 -*-
"""
关键词搜索 - 在全量 phase2 Excel 文件中搜索招标公告。
支持按客户名称、招标人、公告标题、正文关键词等多字段搜索。
结果以文本形式返回。
"""
import os
import re
import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHASE2_DIR = os.path.join(BASE_DIR, "data", "phase2")

# Excel 列顺序（与 pipeline_v3._COLUMNS 一致）
FIELD_KEYS = [
    "title", "tenderer", "date", "result_due", "amount",
    "is_it", "public_due", "source", "matched", "url",
]


def _read_all_records() -> list:
    """读取 PHASE2_DIR 下所有 Excel 文件的全部记录"""
    records = []
    if not os.path.exists(PHASE2_DIR):
        return records
    xlsx_files = sorted(f for f in os.listdir(PHASE2_DIR)
                        if f.lower().endswith(".xlsx") and not f.startswith("~$"))
    for name in xlsx_files:
        path = os.path.join(PHASE2_DIR, name)
        try:
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                record = {"_file": name}
                for i, k in enumerate(FIELD_KEYS):
                    record[k] = str(row[i]) if i < len(row) and row[i] else ""
                records.append(record)
            wb.close()
        except Exception as e:
            print(f"[search] 读取失败 {name}: {e}")
    return records


def search(keyword: str, fields: list = None, match_mode: str = "any") -> dict:
    """
    在全量 Excel 文件中搜索关键词。
    keyword:    搜索关键词（多个关键词用空格分隔）
    fields:     搜索字段列表（默认搜索全部字段）
                 可选: title, tenderer, date, result_due, amount,
                       is_it, public_due, source, matched, url
    match_mode: 匹配模式 "any"（任一关键词匹配）或 "all"（所有关键词都匹配）
    返回：{"total": N, "results": [...], "scanned_files": N}
    """
    if not keyword or not keyword.strip():
        return {"total": 0, "results": [], "scanned_files": 0, "error": "关键词为空"}

    keywords = [k.strip().lower() for k in keyword.split() if k.strip()]
    if not keywords:
        return {"total": 0, "results": [], "scanned_files": 0, "error": "关键词为空"}

    if fields is None:
        # 默认搜索：标题、招标人、客户匹配、来源
        fields = ["title", "tenderer", "matched", "source"]

    records = _read_all_records()
    scanned_files = len(set(r.get("_file", "") for r in records))

    results = []
    for r in records:
        matched_flags = []
        for kw in keywords:
            kw_matched = False
            for field in fields:
                val = str(r.get(field, "")).lower()
                if kw in val:
                    kw_matched = True
                    break
            matched_flags.append(kw_matched)

        if match_mode == "all":
            is_match = all(matched_flags)
        else:
            is_match = any(matched_flags)

        if is_match:
            results.append({
                "title":      r.get("title", ""),
                "tenderer":   r.get("tenderer", ""),
                "date":       r.get("date", ""),
                "amount":     r.get("amount", ""),
                "is_it":      r.get("is_it", ""),
                "matched":    r.get("matched", ""),
                "source":     r.get("source", ""),
                "url":        r.get("url", ""),
                "file":       r.get("_file", ""),
            })

    return {
        "total": len(results),
        "results": results,
        "scanned_files": scanned_files,
        "keyword": keyword,
        "fields": fields,
        "match_mode": match_mode,
    }


def format_search_text(result: dict) -> str:
    """将搜索结果格式化为纯文本"""
    if result.get("error"):
        return f"搜索失败: {result['error']}"

    lines = []
    lines.append(f"搜索关键词: {result.get('keyword', '')}")
    lines.append(f"匹配模式: {'全部匹配' if result.get('match_mode') == 'all' else '任一匹配'}")
    lines.append(f"扫描文件: {result.get('scanned_files', 0)} 个")
    lines.append(f"匹配结果: {result.get('total', 0)} 条")
    lines.append("=" * 60)

    for i, r in enumerate(result.get("results", []), 1):
        lines.append(f"\n【{i}】{r.get('title', '')}")
        lines.append(f"  招标人: {r.get('tenderer', '')}")
        lines.append(f"  发布日期: {r.get('date', '')}")
        lines.append(f"  预算金额: {r.get('amount', '')}")
        lines.append(f"  信息化: {r.get('is_it', '')}")
        lines.append(f"  客户匹配: {r.get('matched', '')}")
        lines.append(f"  来源: {r.get('source', '')}")
        lines.append(f"  链接: {r.get('url', '')}")
        lines.append(f"  文件: {r.get('file', '')}")

    return "\n".join(lines)
