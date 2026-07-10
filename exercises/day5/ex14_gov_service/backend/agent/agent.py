"""
Government Service Full-Chain Agent - Multi-Agent System
Orchestrates multiple LCEL chains for complex workflows.
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import settings


def qa_agent_chain():
    """问答理解Agent"""
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
        ("system", "理解用户需求，提取关键信息，判断业务类型"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def recommendation_agent_chain():
    """业务推荐Agent"""
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
        ("system", "根据用户需求推荐合适的办理渠道和方案"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def form_filling_agent_chain():
    """表单填写Agent"""
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
        ("system", "辅助填写政务表单，预填已知信息"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def verification_agent_chain():
    """材料审核Agent"""
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
        ("system", "审核用户提交的材料是否齐全和合规"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()

def review_agent_chain():
    """业务复核Agent"""
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
        ("system", "最终复核并给出办理建议"),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()


def create_agent():
    """Create multi-agent system."""
    if not settings.is_configured():
        return None
    chains = {}
    chains["qa_agent"] = qa_agent_chain()
    chains["recommendation_agent"] = recommendation_agent_chain()
    chains["form_filling_agent"] = form_filling_agent_chain()
    chains["verification_agent"] = verification_agent_chain()
    chains["review_agent"] = review_agent_chain()
    return chains


def chat(agent, question: str) -> Dict[str, Any]:
    """Run multi-agent workflow."""
    chains = agent
    results = {}
    try:
        result_qa_agent = chains["qa_agent"].invoke({"input": question})
        results["qa_agent"] = result_qa_agent
    except Exception as e:
        results["qa_agent"] = f"[Error] {str(e)}"
    try:
        result_recommendation_agent = chains["recommendation_agent"].invoke({"input": question})
        results["recommendation_agent"] = result_recommendation_agent
    except Exception as e:
        results["recommendation_agent"] = f"[Error] {str(e)}"
    try:
        result_form_filling_agent = chains["form_filling_agent"].invoke({"input": question})
        results["form_filling_agent"] = result_form_filling_agent
    except Exception as e:
        results["form_filling_agent"] = f"[Error] {str(e)}"
    try:
        result_verification_agent = chains["verification_agent"].invoke({"input": question})
        results["verification_agent"] = result_verification_agent
    except Exception as e:
        results["verification_agent"] = f"[Error] {str(e)}"
    try:
        result_review_agent = chains["review_agent"].invoke({"input": question})
        results["review_agent"] = result_review_agent
    except Exception as e:
        results["review_agent"] = f"[Error] {str(e)}"

    # Combine results
    combined = "\n\n---\n\n".join([
        f"## {name}\n{results[name]}"
        for name in results
    ])
    return {"answer": combined, "error": None}
