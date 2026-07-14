"""
Consumer AI Ops Skill Tool - 3 modules: BI + CS + Marketing
Usage:
    from tools.tool import (
        consumer_bi_analyze, consumer_bi_dashboard,
        consumer_cs_chat, consumer_cs_faq, consumer_cs_stats,
        consumer_mk_segmentation, consumer_mk_persona, consumer_mk_sentiment,
        consumer_mk_strategy, consumer_mk_simulate,
        consumer_health_check,
    )
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

from config import check_config
from data_loader import DataLoader


# ============================================================
# Health Check
# ============================================================

def consumer_health_check() -> str:
    """检查LLM配置状态和数据加载状态。"""
    return json.dumps({
        "llm_configured": check_config(),
        "data_loaded": bool(DataLoader.sales()),
        "modules": ["bi_analysis", "customer_service", "marketing_strategy"] if check_config() else [],
    }, ensure_ascii=False, indent=2)


# ============================================================
# BI Analysis Module (ReAct Agent)
# ============================================================

def consumer_bi_analyze(question: str) -> str:
    """BI智能分析：输入自然语言问题，ReAct Agent自动调用数据工具（查询销售/客户/统计/图表）并返回分析结果。"""
    from services.bi_engine import bi_analyze
    result = bi_analyze(question)
    return json.dumps(result, ensure_ascii=False, indent=2)


def consumer_bi_dashboard() -> str:
    """获取BI仪表盘预计算数据：KPI指标、月度趋势、品类占比、区域对比、交叉分析热力图。"""
    return json.dumps(DataLoader.dashboard_summary(), ensure_ascii=False, indent=2)


# ============================================================
# Customer Service Module (RAG + Multi-Agent)
# ============================================================

def consumer_cs_chat(question: str, session_id: str = "") -> str:
    """智能客服对话：4-Agent流水线（意图分类→RAG检索→答案生成→情感分析+工单创建），支持多轮对话。"""
    from services.cs_engine import cs_chat
    result = cs_chat(question, session_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


def consumer_cs_faq(category: str = "") -> str:
    """获取FAQ列表，可按分类筛选。返回问题、答案和分类信息。"""
    from services.cs_engine import get_faq_suggestions
    items = get_faq_suggestions(category or None)
    return json.dumps({"items": items}, ensure_ascii=False, indent=2)


def consumer_cs_stats() -> str:
    """获取客服统计：今日咨询量、满意度、待处理工单、FAQ分类、服务指标。"""
    return json.dumps(DataLoader.cs_stats(), ensure_ascii=False, indent=2)


# ============================================================
# Marketing Module (Structured Output + Computed)
# ============================================================

def consumer_mk_segmentation() -> str:
    """RFM客户分群数据：6个分群的客户数、平均LTV、流失风险分布等。纯计算，无需LLM。"""
    from services.marketing_engine import analyze_segmentation
    return json.dumps(analyze_segmentation(), ensure_ascii=False, indent=2)


def consumer_mk_persona(customer_id: str) -> str:
    """生成客户画像：消费偏好、风险因素、推荐动作、预估LTV、偏好渠道。LLM驱动，PydanticOutputParser结构化输出。"""
    from services.marketing_engine import generate_persona
    result = generate_persona(customer_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


def consumer_mk_sentiment(category: str = "") -> str:
    """评论情感分析：按品类的正/中/负面分布、整体满意度。LLM驱动，PydanticOutputParser结构化输出。"""
    from services.marketing_engine import analyze_sentiment
    result = analyze_sentiment(category or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


def consumer_mk_strategy(segment: str = "高价值沉睡", objective: str = "提升客户活跃度和复购率") -> str:
    """生成营销策略：活动名称、目标人群、渠道、核心信息、优惠设计、预算、预期ROI、时间线。LLM驱动。"""
    from services.marketing_engine import generate_strategy
    result = generate_strategy(segment, objective)
    return json.dumps(result, ensure_ascii=False, indent=2)


def consumer_mk_simulate(budget: float = 50000, target_segment: str = "", channel_mix: dict = None) -> str:
    """ROI蒙特卡洛模拟：输入预算、目标分群、渠道配比，模拟1000次ROI分布，输出P10/P50/P90和正收益概率。"""
    from services.marketing_engine import simulate_roi
    result = simulate_roi(budget, target_segment or None, channel_mix)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# CLI Entry
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Consumer AI Ops Skill Tool")
    parser.add_argument("action", choices=[
        "health", "bi", "dashboard",
        "cs", "faq", "stats",
        "segmentation", "persona", "sentiment", "strategy", "simulate"
    ], help="Action to perform")
    parser.add_argument("-q", "--question", help="Question for BI or CS")
    parser.add_argument("--customer-id", help="Customer ID for persona")
    parser.add_argument("--segment", help="Target segment")
    parser.add_argument("--objective", help="Marketing objective")
    parser.add_argument("--budget", type=float, default=50000, help="Budget for ROI simulation")
    parser.add_argument("--category", help="Category filter")
    args = parser.parse_args()

    if args.action == "health":
        print(consumer_health_check())
    elif args.action == "bi":
        if not args.question:
            print("Please provide -q"); sys.exit(1)
        print(consumer_bi_analyze(args.question))
    elif args.action == "dashboard":
        print(consumer_bi_dashboard())
    elif args.action == "cs":
        if not args.question:
            print("Please provide -q"); sys.exit(1)
        print(consumer_cs_chat(args.question))
    elif args.action == "faq":
        print(consumer_cs_faq(args.category or ""))
    elif args.action == "stats":
        print(consumer_cs_stats())
    elif args.action == "segmentation":
        print(consumer_mk_segmentation())
    elif args.action == "persona":
        if not args.customer_id:
            print("Please provide --customer-id"); sys.exit(1)
        print(consumer_mk_persona(args.customer_id))
    elif args.action == "sentiment":
        print(consumer_mk_sentiment(args.category or ""))
    elif args.action == "strategy":
        print(consumer_mk_strategy(args.segment or "高价值沉睡", args.objective or "提升复购率"))
    elif args.action == "simulate":
        print(consumer_mk_simulate(args.budget))
