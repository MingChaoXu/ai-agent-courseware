"""
Comprehensive Roadshow Agent - Multi-Agent System
Orchestrates multiple LCEL chains for complex workflows.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


def scenario_agent_chain():
    """场景分析Agent(20%)"""
    if not settings.is_configured():
        return None
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "分析业务场景痛点、用户需求、现有方案不足"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def solution_agent_chain():
    """技术方案Agent(30%)"""
    if not settings.is_configured():
        return None
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "输出技术架构、核心算法、数据流程"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def demo_agent_chain():
    """Demo演示Agent(30%)"""
    if not settings.is_configured():
        return None
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "生成可交互的演示流程"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def value_agent_chain():
    """商业价值Agent(20%)"""
    if not settings.is_configured():
        return None
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "量化ROI、社会效益、推广价值"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()


def create_agent():
    """Create multi-agent system."""
    if not settings.is_configured():
        return None
    chains = {}
    chains["scenario_agent"] = scenario_agent_chain()
    chains["solution_agent"] = solution_agent_chain()
    chains["demo_agent"] = demo_agent_chain()
    chains["value_agent"] = value_agent_chain()
    return chains


def chat(agent, question: str) -> Dict[str, Any]:
    """Run multi-agent workflow."""
    chains = agent
    results = {}
    try:
        result_scenario_agent = chains["scenario_agent"].invoke({"input": question})
        results["scenario_agent"] = result_scenario_agent
    except Exception as e:
        results["scenario_agent"] = f"[Error] {str(e)}"
    try:
        result_solution_agent = chains["solution_agent"].invoke({"input": question})
        results["solution_agent"] = result_solution_agent
    except Exception as e:
        results["solution_agent"] = f"[Error] {str(e)}"
    try:
        result_demo_agent = chains["demo_agent"].invoke({"input": question})
        results["demo_agent"] = result_demo_agent
    except Exception as e:
        results["demo_agent"] = f"[Error] {str(e)}"
    try:
        result_value_agent = chains["value_agent"].invoke({"input": question})
        results["value_agent"] = result_value_agent
    except Exception as e:
        results["value_agent"] = f"[Error] {str(e)}"

    # Combine results
    combined = "\n\n---\n\n".join([
        f"## {name}\n{results[name]}"
        for name in results
    ])
    return {"answer": combined, "error": None}
