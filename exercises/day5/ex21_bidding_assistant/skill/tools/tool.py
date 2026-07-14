"""
Bidding Assistant Skill Tool - Pipeline + Search + Config
Usage:
    from tools.tool import (
        bidding_run_pipeline,
        bidding_run_phase1,
        bidding_run_phase2,
        bidding_search,
        bidding_list_files,
        bidding_health_check,
        bidding_get_config,
    )
"""

import os
import sys
import json
import argparse
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


# ============================================================
# Health Check
# ============================================================

def bidding_health_check() -> str:
    """Check system health: pipeline modules, data directories, and collection source availability."""
    result = {
        "pipeline_v3": False,
        "config": False,
        "search": False,
        "merge": False,
        "health": False,
        "directories": {},
        "sources": {},
    }

    try:
        import pipeline_v3
        result["pipeline_v3"] = True
    except Exception as e:
        result["pipeline_v3_error"] = str(e)

    try:
        import config as _config
        result["config"] = True
        cfg = _config.load_config()
        result["config_values"] = cfg
    except Exception as e:
        result["config_error"] = str(e)

    try:
        import search as _search
        result["search"] = True
    except Exception as e:
        result["search_error"] = str(e)

    try:
        import merge as _merge
        result["merge"] = True
    except Exception as e:
        result["merge_error"] = str(e)

    try:
        import health as _health
        result["health"] = True
        sources = _health.check_all_sources()
        result["sources"] = sources
    except Exception as e:
        result["health_error"] = str(e)

    base_dir = str(_BACKEND_DIR)
    for d in ("data", "data/phase1", "data/phase2"):
        full = os.path.join(base_dir, d.replace("/", os.sep))
        result["directories"][d] = os.path.exists(full)

    kehu_path = os.path.join(base_dir, "kehu-0619.xlsx")
    result["kehu_file_exists"] = os.path.exists(kehu_path)

    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# Pipeline Execution
# ============================================================

def bidding_run_pipeline() -> str:
    """Run the full pipeline: Phase 1 (collect from 6 sources) + Phase 2 (LLM extract + customer match). Returns summary with output file paths."""
    from pipeline_v3 import run_full_pipeline, PHASE1_DIR, PHASE2_DIR

    final = run_full_pipeline()

    phase1_files = sorted(os.listdir(PHASE1_DIR)) if os.path.exists(PHASE1_DIR) else []
    phase2_files = sorted(os.listdir(PHASE2_DIR)) if os.path.exists(PHASE2_DIR) else []

    return json.dumps({
        "status": "completed" if final else "no_data",
        "total_processed": len(final),
        "phase1_files": phase1_files,
        "phase2_files": phase2_files,
    }, ensure_ascii=False, indent=2)


def bidding_run_phase1() -> str:
    """Run Phase 1 only: collect bid announcements from 6 government procurement sources using Selenium. Returns collected count and output file path."""
    from pipeline_v3 import run_phase1

    collected, output_file = run_phase1()

    return json.dumps({
        "status": "completed" if collected else "no_data",
        "total_collected": len(collected),
        "output_file": output_file,
        "sources": {},
    }, ensure_ascii=False, indent=2)


def bidding_run_phase2(input_file: str = "") -> str:
    """Run Phase 2 only: LLM field extraction (amount/category/deadlines/tenderer) + customer matching. If input_file not specified, uses the latest Phase 1 output."""
    from pipeline_v3 import run_phase2, PHASE1_DIR

    if not input_file:
        if not os.path.exists(PHASE1_DIR):
            return json.dumps({"error": "Phase1 directory not found, run Phase 1 first"}, ensure_ascii=False)
        files = sorted(
            [f for f in os.listdir(PHASE1_DIR) if f.endswith(".json")],
            reverse=True,
        )
        if not files:
            return json.dumps({"error": "No Phase 1 output files found"}, ensure_ascii=False)
        input_file = os.path.join(PHASE1_DIR, files[0])

    if not os.path.exists(input_file):
        return json.dumps({"error": f"Input file not found: {input_file}"}, ensure_ascii=False)

    final = run_phase2(input_file)

    return json.dumps({
        "status": "completed" if final else "no_data",
        "total_processed": len(final),
        "input_file": input_file,
    }, ensure_ascii=False, indent=2)


# ============================================================
# Search
# ============================================================

def bidding_search(keyword: str, category: str = "phase2") -> str:
    """Search collected bidding data by keyword. Searches across title, tenderer, amount, category fields. Returns matched records with source file info."""
    import search as _search

    result = _search.search(keyword)
    text = _search.format_search_text(result)

    return json.dumps({
        "keyword": keyword,
        "total_matches": result.get("total", 0),
        "text_output": text,
        "matches": result.get("matches", []),
    }, ensure_ascii=False, indent=2)


# ============================================================
# File Management
# ============================================================

def bidding_list_files(phase: str = "phase2") -> str:
    """List output files for Phase 1 (JSON) or Phase 2 (Excel). Returns file names, sizes, and modification times."""
    base_dir = str(_BACKEND_DIR)
    phase_dir = os.path.join(base_dir, "data", phase)

    if not os.path.exists(phase_dir):
        return json.dumps({"phase": phase, "files": [], "error": "Directory not found"}, ensure_ascii=False)

    ext = ".json" if phase == "phase1" else ".xlsx"
    files = []
    for name in sorted(os.listdir(phase_dir)):
        if not name.lower().endswith(ext) or name.startswith("~$"):
            continue
        path = os.path.join(phase_dir, name)
        stat = os.stat(path)
        from datetime import datetime
        files.append({
            "name": name,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })

    return json.dumps({"phase": phase, "total": len(files), "files": files}, ensure_ascii=False, indent=2)


# ============================================================
# Configuration
# ============================================================

def bidding_get_config() -> str:
    """Get current system configuration: similarity threshold, schedule enabled, AI verify toggle."""
    import config as _config

    cfg = _config.load_config()
    return json.dumps(cfg, ensure_ascii=False, indent=2)


# ============================================================
# CLI
# ============================================================

def _cli():
    parser = argparse.ArgumentParser(description="Bidding Assistant Skill Tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Health check")
    sub.add_parser("pipeline", help="Run full pipeline (Phase 1 + Phase 2)")
    sub.add_parser("phase1", help="Run Phase 1 only (collect)")
    p2 = sub.add_parser("phase2", help="Run Phase 2 only (process)")
    p2.add_argument("--input", default="", help="Input JSON file path")

    sp = sub.add_parser("search", help="Search collected data")
    sp.add_argument("-k", "--keyword", required=True, help="Search keyword")

    lf = sub.add_parser("files", help="List output files")
    lf.add_argument("--phase", default="phase2", choices=["phase1", "phase2"])

    sub.add_parser("config", help="Get current configuration")

    args = parser.parse_args()

    if args.command == "health":
        print(bidding_health_check())
    elif args.command == "pipeline":
        print(bidding_run_pipeline())
    elif args.command == "phase1":
        print(bidding_run_phase1())
    elif args.command == "phase2":
        print(bidding_run_phase2(args.input))
    elif args.command == "search":
        print(bidding_search(args.keyword))
    elif args.command == "files":
        print(bidding_list_files(args.phase))
    elif args.command == "config":
        print(bidding_get_config())
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
