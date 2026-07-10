"""
Social Governance Multi-Agent - Multi-Agent System
Orchestrates multiple LCEL chains for complex workflows.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


def event_entry_agent_chain():
    """事件录入Agent"""
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
        ("system", "录入社会治理事件，分类归档"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def legal_consultation_agent_chain():
    """法律咨询Agent"""
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
        ("system", "为纠纷类事件提供法律咨询建议（条件触发：仅纠纷类）"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def brief_generation_agent_chain():
    """通报生成Agent"""
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
        ("system", "生成社会治理通报"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def alert_agent_chain():
    """预警处置Agent"""
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
        ("system", "评估事件风险等级，触发预警"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()


def create_agent():
    """Create multi-agent system."""
    if not settings.is_configured():
        return None
    chains = {}
    chains["event_entry_agent"] = event_entry_agent_chain()
    chains["legal_consultation_agent"] = legal_consultation_agent_chain()
    chains["brief_generation_agent"] = brief_generation_agent_chain()
    chains["alert_agent"] = alert_agent_chain()
    return chains


def chat(agent, question: str) -> Dict[str, Any]:
    """Run multi-agent workflow."""
    chains = agent
    results = {}
    try:
        result_event_entry_agent = chains["event_entry_agent"].invoke({"input": question})
        results["event_entry_agent"] = result_event_entry_agent
    except Exception as e:
        results["event_entry_agent"] = f"[Error] {str(e)}"
    try:
        result_legal_consultation_agent = chains["legal_consultation_agent"].invoke({"input": question})
        results["legal_consultation_agent"] = result_legal_consultation_agent
    except Exception as e:
        results["legal_consultation_agent"] = f"[Error] {str(e)}"
    try:
        result_brief_generation_agent = chains["brief_generation_agent"].invoke({"input": question})
        results["brief_generation_agent"] = result_brief_generation_agent
    except Exception as e:
        results["brief_generation_agent"] = f"[Error] {str(e)}"
    try:
        result_alert_agent = chains["alert_agent"].invoke({"input": question})
        results["alert_agent"] = result_alert_agent
    except Exception as e:
        results["alert_agent"] = f"[Error] {str(e)}"

    # Combine results
    combined = "\n\n---\n\n".join([
        f"## {name}\n{results[name]}"
        for name in results
    ])
    return {"answer": combined, "error": None}
