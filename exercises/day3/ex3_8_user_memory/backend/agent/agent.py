"""
User Memory Management Agent - Multi-Agent System
Orchestrates multiple LCEL chains for complex workflows.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


def memory_agent_chain():
    """用户记忆管理Agent"""
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
        ("system", "管理用户档案信息，包括基本信息、偏好和历史记录"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def qa_agent_chain():
    """问答Agent"""
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
        ("system", "基于用户记忆和历史记录回答问题"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def update_agent_chain():
    """信息更新Agent"""
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
        ("system", "解析用户输入，更新用户档案"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()


def create_agent():
    """Create multi-agent system."""
    if not settings.is_configured():
        return None
    chains = {}
    chains["memory_agent"] = memory_agent_chain()
    chains["qa_agent"] = qa_agent_chain()
    chains["update_agent"] = update_agent_chain()
    return chains


def chat(agent, question: str) -> Dict[str, Any]:
    """Run multi-agent workflow."""
    chains = agent
    results = {}
    try:
        result_memory_agent = chains["memory_agent"].invoke({"input": question})
        results["memory_agent"] = result_memory_agent
    except Exception as e:
        results["memory_agent"] = f"[Error] {str(e)}"
    try:
        result_qa_agent = chains["qa_agent"].invoke({"input": question})
        results["qa_agent"] = result_qa_agent
    except Exception as e:
        results["qa_agent"] = f"[Error] {str(e)}"
    try:
        result_update_agent = chains["update_agent"].invoke({"input": question})
        results["update_agent"] = result_update_agent
    except Exception as e:
        results["update_agent"] = f"[Error] {str(e)}"

    # Combine results
    combined = "\n\n---\n\n".join([
        f"## {name}\n{results[name]}"
        for name in results
    ])
    return {"answer": combined, "error": None}
