"""
Marketing Engine — RFM Segmentation + Sentiment Analysis + Campaign Strategy + ROI Simulation.
"""

import json
import random
import math
from typing import Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser

from config import get_llm, check_config
from data_loader import DataLoader


# ═══════════════════════════════════════════════════════════
# Pydantic Models for structured output
# ═══════════════════════════════════════════════════════════

class CustomerPersona(BaseModel):
    """Customer persona with detailed profile."""
    customer_id: str = Field(description="客户ID")
    segment: str = Field(description="RFM分群名称")
    profile_summary: str = Field(description="一句话画像总结")
    consumption_preference: str = Field(description="消费偏好描述")
    risk_factors: list[str] = Field(description="风险因素列表")
    recommended_actions: list[str] = Field(description="推荐运营动作")
    estimated_ltv: str = Field(description="预估LTV等级：高/中/低")
    preferred_channel: str = Field(description="最佳触达渠道")


class SentimentReport(BaseModel):
    """Sentiment analysis report."""
    overall_sentiment: str = Field(description="整体情感倾向：正面/中性/负面")
    positive_ratio: float = Field(description="正面评价占比")
    negative_keywords: list[str] = Field(description="负面关键词")
    positive_keywords: list[str] = Field(description="正面关键词")
    hot_issues: list[str] = Field(description="热点问题列表")
    risk_alerts: list[str] = Field(description="风险预警")
    action_suggestions: list[str] = Field(description="行动建议")


class CampaignStrategy(BaseModel):
    """Marketing campaign strategy."""
    target_segment: str = Field(description="目标客群")
    campaign_name: str = Field(description="活动名称")
    objective: str = Field(description="活动目标")
    channels: list[str] = Field(description="投放渠道")
    key_message: str = Field(description="核心话术")
    offer_design: str = Field(description="权益设计")
    expected_reach: str = Field(description="预计触达人数")
    expected_conversion: str = Field(description="预计转化率")
    budget_estimate: str = Field(description="预算估算")
    roi_forecast: str = Field(description="ROI预测")
    timeline: str = Field(description="活动排期")


# ═══════════════════════════════════════════════════════════
# RFM Segmentation Analysis
# ═══════════════════════════════════════════════════════════

def analyze_segmentation() -> dict:
    """Deep RFM segmentation analysis (computed, no LLM needed)."""
    customers = DataLoader.customers()
    segments = {}
    for c in customers:
        seg = c["segment"]
        segments.setdefault(seg, []).append(c)

    analysis = {}
    for seg_name, members in segments.items():
        avg_recency = sum(m["recency_days"] for m in members) / len(members)
        avg_frequency = sum(m["frequency"] for m in members) / len(members)
        avg_monetary = sum(m["monetary"] for m in members) / len(members)
        avg_ltv = sum(m["ltv"] for m in members) / len(members)
        active_rate = sum(1 for m in members if m["is_active"]) / len(members) * 100

        top_categories = {}
        for m in members:
            cat = m["preferred_category"]
            top_categories[cat] = top_categories.get(cat, 0) + 1
        top_3_cats = sorted(top_categories.items(), key=lambda x: -x[1])[:3]

        analysis[seg_name] = {
            "count": len(members),
            "percentage": round(len(members) / len(customers) * 100, 1),
            "avg_recency_days": round(avg_recency, 1),
            "avg_frequency": round(avg_frequency, 1),
            "avg_monetary": round(avg_monetary, 2),
            "avg_ltv": round(avg_ltv, 2),
            "active_rate": round(active_rate, 1),
            "top_categories": [{"category": c, "count": n} for c, n in top_3_cats],
            "churn_risk_distribution": {
                "高": sum(1 for m in members if m["churn_risk"] == "高"),
                "中": sum(1 for m in members if m["churn_risk"] == "中"),
                "低": sum(1 for m in members if m["churn_risk"] == "低"),
            },
        }

    return analysis


# ═══════════════════════════════════════════════════════════
# Customer Persona Generation (LLM)
# ═══════════════════════════════════════════════════════════

def generate_persona(customer_id: str) -> dict:
    """Generate a detailed customer persona using LLM."""
    if not check_config():
        return {"error": "LLM未配置"}

    # Find customer
    customer = None
    for c in DataLoader.customers():
        if c["id"] == customer_id:
            customer = c
            break
    if not customer:
        return {"error": f"客户 {customer_id} 不存在"}

    llm = get_llm(temperature=0.3)
    parser = PydanticOutputParser(pydantic_object=CustomerPersona)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是客户画像分析专家。根据客户数据生成精准画像。\n\n"
         "{format_instructions}\n\n"
         "注意：所有字段都必须填写，不能为空。分析要基于数据，推理要合理。"),
        ("human", "客户数据：{customer_data}"),
    ])

    chain = prompt | llm | parser
    try:
        persona = chain.invoke({
            "customer_data": json.dumps(customer, ensure_ascii=False, indent=2),
            "format_instructions": parser.get_format_instructions(),
        })
        return persona.model_dump()
    except Exception as e:
        # Fallback to text output
        text_chain = prompt | llm | StrOutputParser()
        text_result = text_chain.invoke({
            "customer_data": json.dumps(customer, ensure_ascii=False, indent=2),
            "format_instructions": parser.get_format_instructions(),
        })
        return {"raw_text": text_result, "error": str(e)}


# ═══════════════════════════════════════════════════════════
# Sentiment Analysis (LLM)
# ═══════════════════════════════════════════════════════════

def analyze_sentiment(category: str = None) -> dict:
    """Analyze reviews sentiment with LLM structured output."""
    if not check_config():
        return {"error": "LLM未配置"}

    reviews = DataLoader.reviews()
    if category:
        reviews = [r for r in reviews if r["category"] == category]

    if not reviews:
        return {"error": "没有找到相关评价数据"}

    review_summary = json.dumps([
        {"rating": r["rating"], "content": r["content"], "sentiment": r["sentiment"], "category": r["category"]}
        for r in reviews
    ], ensure_ascii=False)

    llm = get_llm(temperature=0.2)
    parser = PydanticOutputParser(pydantic_object=SentimentReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是消费品牌舆情分析师。分析用户评价数据，输出结构化报告。\n\n"
         "{format_instructions}\n\n"
         "注意：基于数据客观分析，负面关键词和风险预警要具体。"),
        ("human", "评价数据：{review_data}"),
    ])

    chain = prompt | llm | parser
    try:
        report = chain.invoke({
            "review_data": review_summary,
            "format_instructions": parser.get_format_instructions(),
        })
        return report.model_dump()
    except Exception as e:
        text_chain = prompt | llm | StrOutputParser()
        text_result = text_chain.invoke({
            "review_data": review_summary,
            "format_instructions": parser.get_format_instructions(),
        })
        return {"raw_text": text_result, "error": str(e)}


# ═══════════════════════════════════════════════════════════
# Campaign Strategy Generation (LLM)
# ═══════════════════════════════════════════════════════════

def generate_strategy(segment: str = None, objective: str = None) -> dict:
    """Generate marketing campaign strategy."""
    if not check_config():
        return {"error": "LLM未配置"}

    seg_analysis = analyze_segmentation()
    if segment and segment in seg_analysis:
        seg_data = seg_analysis[segment]
    else:
        # Pick the most actionable segment
        seg_data = seg_analysis.get("高价值沉睡", list(seg_analysis.values())[0])
        segment = segment or "高价值沉睡"

    objective = objective or "提升客户活跃度和复购率"

    llm = get_llm(temperature=0.4)
    parser = PydanticOutputParser(pydantic_object=CampaignStrategy)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是资深营销策略师，擅长消费品牌精准营销。根据客群数据和目标，设计可执行的营销方案。\n\n"
         "{format_instructions}\n\n"
         "要求：策略要具体、可执行，预算和ROI要有合理依据。"),
        ("human",
         "目标客群：{segment}\n"
         "客群数据：{seg_data}\n"
         "营销目标：{objective}"),
    ])

    chain = prompt | llm | parser
    try:
        strategy = chain.invoke({
            "segment": segment,
            "seg_data": json.dumps(seg_data, ensure_ascii=False),
            "objective": objective,
            "format_instructions": parser.get_format_instructions(),
        })
        return strategy.model_dump()
    except Exception as e:
        text_chain = prompt | llm | StrOutputParser()
        text_result = text_chain.invoke({
            "segment": segment,
            "seg_data": json.dumps(seg_data, ensure_ascii=False),
            "objective": objective,
            "format_instructions": parser.get_format_instructions(),
        })
        return {"raw_text": text_result, "error": str(e)}


# ═══════════════════════════════════════════════════════════
# ROI Simulation (computed, no LLM)
# ═══════════════════════════════════════════════════════════

def simulate_roi(budget: float, target_segment: str = "高价值沉睡",
                 channel_mix: dict = None) -> dict:
    """
    Simulate campaign ROI based on budget allocation and segment characteristics.
    channel_mix: {"线上直营": 0.5, "线上分销": 0.3, "线下门店": 0.2}
    """
    if not channel_mix:
        channel_mix = {"线上直营": 0.5, "线上分销": 0.3, "线下门店": 0.2}

    customers = DataLoader.customers()
    seg_customers = [c for c in customers if c["segment"] == target_segment]
    seg_count = len(seg_customers)

    if seg_count == 0:
        return {"error": f"找不到 {target_segment} 客群"}

    avg_monetary = sum(c["monetary"] for c in seg_customers) / seg_count
    active_rate = sum(1 for c in seg_customers if c["is_active"]) / seg_count

    # Simulation parameters (based on industry benchmarks)
    base_reach_rate = 0.65  # 消息触达率
    channel_conversion = {"线上直营": 0.035, "线上分销": 0.025, "线下门店": 0.05}
    avg_order_value = avg_monetary / max(sum(c["frequency"] for c in seg_customers) / seg_count, 1)

    # Calculate per-channel
    channel_results = {}
    total_reach = 0
    total_conversion = 0
    total_revenue = 0

    for ch, ratio in channel_mix.items():
        ch_budget = budget * ratio
        # CPM / CPC estimates
        if "线上" in ch:
            cost_per_reach = 2.5  # 元/人
        else:
            cost_per_reach = 8.0  # 线下成本更高

        reaches = int(ch_budget / cost_per_reach)
        conv_rate = channel_conversion.get(ch, 0.03) * (1 + active_rate)
        conversions = int(reaches * conv_rate)
        revenue = conversions * avg_order_value * random.uniform(0.8, 1.2)

        channel_results[ch] = {
            "budget": round(ch_budget, 2),
            "reaches": reaches,
            "conversions": conversions,
            "revenue": round(revenue, 2),
            "roi": round((revenue - ch_budget) / max(ch_budget, 1) * 100, 1),
            "cpa": round(ch_budget / max(conversions, 1), 2),
        }
        total_reach += reaches
        total_conversion += conversions
        total_revenue += revenue

    overall_roi = round((total_revenue - budget) / max(budget, 1) * 100, 1)

    # Monte Carlo: run 100 simulations
    sim_results = []
    for _ in range(100):
        sim_revenue = total_revenue * random.uniform(0.6, 1.4)
        sim_roi = round((sim_revenue - budget) / max(budget, 1) * 100, 1)
        sim_results.append(sim_roi)

    sim_results.sort()
    p10 = sim_results[10]
    p50 = sim_results[50]
    p90 = sim_results[90]

    return {
        "budget": budget,
        "target_segment": target_segment,
        "target_count": seg_count,
        "channel_mix": channel_mix,
        "channel_results": channel_results,
        "total_reach": total_reach,
        "total_conversion": total_conversion,
        "total_revenue": round(total_revenue, 2),
        "overall_roi": overall_roi,
        "net_profit": round(total_revenue - budget, 2),
        "monte_carlo": {
            "p10_roi": p10,
            "p50_roi": p50,
            "p90_roi": p90,
            "positive_prob": round(sum(1 for r in sim_results if r > 0) / len(sim_results) * 100, 1),
        },
        "recommendation": "建议加大线上直营投放" if overall_roi > 100 else (
            "建议优化渠道组合提升转化" if overall_roi > 0 else "当前策略ROI为负，建议调整目标客群或降低预算"
        ),
    }
