"""
Event-Driven Agent Practice - Multi-Agent System
Orchestrates multiple LCEL chains for complex workflows.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


def timer_agent_chain():
    """定时触发Agent"""
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
        ("system", "按计划时间触发业务流程，如每日商机跟进提醒"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def data_alert_agent_chain():
    """数据触发Agent"""
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
        ("system", "监测数据指标，超阈值时自动告警"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def external_event_agent_chain():
    """外部触发Agent"""
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
        ("system", "响应外部系统事件，启动业务流程"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()


def create_agent():
    """Create multi-agent system."""
    if not settings.is_configured():
        return None
    chains = {}
    chains["timer_agent"] = timer_agent_chain()
    chains["data_alert_agent"] = data_alert_agent_chain()
    chains["external_event_agent"] = external_event_agent_chain()
    return chains


def chat(agent, question: str) -> Dict[str, Any]:
    """Run multi-agent workflow."""
    chains = agent
    results = {}
    try:
        result_timer_agent = chains["timer_agent"].invoke({"input": question})
        results["timer_agent"] = result_timer_agent
    except Exception as e:
        results["timer_agent"] = f"[Error] {str(e)}"
    try:
        result_data_alert_agent = chains["data_alert_agent"].invoke({"input": question})
        results["data_alert_agent"] = result_data_alert_agent
    except Exception as e:
        results["data_alert_agent"] = f"[Error] {str(e)}"
    try:
        result_external_event_agent = chains["external_event_agent"].invoke({"input": question})
        results["external_event_agent"] = result_external_event_agent
    except Exception as e:
        results["external_event_agent"] = f"[Error] {str(e)}"

    # Combine results
    combined = "\n\n---\n\n".join([
        f"## {name}\n{results[name]}"
        for name in results
    ])
    return {"answer": combined, "error": None}
