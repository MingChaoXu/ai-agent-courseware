"""
培训课程 - 公共工具函数
所有课题共用的 LLM/Embedding 创建、API 配置检查等。
"""

import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from dotenv import load_dotenv
from pathlib import Path

# 加载 .env（从项目根目录）
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)

# LangChain 核心组件
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_llm(temperature: float = 0.3, max_tokens: int = 2000, **kwargs) -> ChatOpenAI:
    """创建 LLM 实例"""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("OPENAI_API_BASE", ""),
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def get_embeddings() -> OpenAIEmbeddings:
    """创建 Embedding 模型实例"""
    return OpenAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small"),
        api_key=os.getenv("EMBEDDING_API_KEY", os.getenv("OPENAI_API_KEY", "")),
        base_url=os.getenv("EMBEDDING_API_BASE", os.getenv("OPENAI_API_BASE", "")),
    )


def format_docs(docs) -> str:
    """将检索到的文档列表格式化为字符串"""
    return "\n\n---\n".join(d.page_content for d in docs)


def check_api_config() -> bool:
    """检查 API 配置"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_API_BASE", "")
    if not api_key or api_key == "sk-your-api-key-here":
        print("[警告] 未配置 OPENAI_API_KEY，请在 .env 文件中设置")
        print(f"  .env 文件位置: {_ENV_PATH}")
        return False
    if not base_url:
        print("[警告] 未配置 OPENAI_API_BASE，请在 .env 文件中设置")
        return False
    print(f"  API 地址: {base_url}")
    print(f"  模型名称: {os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')}")
    print(f"  嵌入模型: {os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-3-small')}")
    print(f"  API Key:  {'已配置 ✓' if api_key else '未配置 ✗'}")
    return True


def build_lcel_chain(system_prompt: str, llm=None):
    """快速构建 LCEL Chain: ChatPromptTemplate -> LLM -> StrOutputParser"""
    if llm is None:
        llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()
