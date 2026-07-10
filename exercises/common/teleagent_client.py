"""
LangChain LLM 智能体客户端（培训课程公共模块）
==================================================
使用 LangChain + OpenAI 兼容接口调用真实 LLM。
提供智能体管理、知识库（FAISS）、技能绑定、工作流编排等功能。

使用前：
  1. pip install -r requirements.txt
  2. 复制 .env.example 为 .env，填入 API 配置
  3. python gen_sample_data.py  （生成样例数据）

环境变量（.env 文件）：
  OPENAI_API_KEY       - API 密钥
  OPENAI_API_BASE      - API 基础地址
  OPENAI_MODEL_NAME    - 模型名称
  EMBEDDING_MODEL_NAME - 嵌入模型名称
"""

import os
import json
import time
import warnings; warnings.filterwarnings("ignore", category=DeprecationWarning)
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# 加载 .env 配置
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

# LangChain 核心组件
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage, BaseMessage
)
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
#  全局配置
# ============================================================

LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_BASE_URL = os.getenv("OPENAI_API_BASE", "")
LLM_MODEL = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_API_BASE", LLM_BASE_URL)
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", LLM_API_KEY)


def _create_llm(temperature: float = 0.3, max_tokens: int = 2000, **kwargs) -> ChatOpenAI:
    """创建 LLM 实例"""
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def _create_embeddings() -> OpenAIEmbeddings:
    """创建 Embedding 模型实例"""
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=EMBEDDING_API_KEY,
        base_url=EMBEDDING_BASE_URL,
    )


def check_config() -> bool:
    """检查 LLM 配置是否完整"""
    if not LLM_API_KEY:
        print("[警告] 未配置 OPENAI_API_KEY，请在 .env 文件中设置。")
        print(f"  .env 文件位置: {_env_path}")
        return False
    if not LLM_BASE_URL:
        print("[警告] 未配置 OPENAI_API_BASE，请在 .env 文件中设置。")
        return False
    return True


# ============================================================
#  内存注册表（模拟平台资源管理）
# ============================================================

_agent_registry: Dict[str, dict] = {}
_kb_registry: Dict[str, dict] = {}
_skill_registry: Dict[str, dict] = {}
_workflow_registry: Dict[str, dict] = {}
_counters = {"agent": 0, "kb": 0, "skill": 0, "workflow": 0}


def _gen_id(prefix: str) -> str:
    _counters[prefix] = _counters.get(prefix, 0) + 1
    return f"{prefix}_{_counters[prefix]}"


# ============================================================
#  LLM 客户端主类
# ============================================================

class TeleAgentClient:
    """
    LangChain 智能体客户端

    封装 LLM 对话、RAG 知识库（FAISS）、技能绑定、多步骤工作流等功能。
    所有资源存储在内存中，适合培训演示使用。
    """

    def __init__(self):
        self.llm = _create_llm()
        check_config()

    # ========== 智能体管理 ==========

    def create_agent(self, name: str, description: str, system_prompt: str,
                     model: str = "default", skills: List[str] = None) -> Dict:
        """创建智能体（返回 ID，内部存储 system_prompt 和对话历史）"""
        agent_id = _gen_id("agent")
        _agent_registry[agent_id] = {
            "id": agent_id,
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "history": [],              # List[BaseMessage]
            "rag_kb_ids": [],           # 绑定的知识库 ID
            "rag_config": {},           # RAG 配置（top_k, temperature 等）
            "skills_meta": skills or [],  # 技能元信息
            "created_at": time.time(),
        }
        return {"id": agent_id, "name": name}

    def list_agents(self) -> List[Dict]:
        """列出所有智能体"""
        return [
            {"id": aid, "name": a["name"], "description": a["description"]}
            for aid, a in _agent_registry.items()
        ]

    def get_agent(self, agent_id: str) -> Dict:
        """获取智能体详情"""
        a = _agent_registry.get(agent_id)
        if not a:
            return {}
        return {"id": a["id"], "name": a["name"],
                "description": a["description"], "system_prompt": a["system_prompt"]}

    def delete_agent(self, agent_id: str) -> bool:
        """删除智能体"""
        if agent_id in _agent_registry:
            del _agent_registry[agent_id]
            return True
        return False

    # ========== 对话 ==========

    def chat(self, agent_id: str, message: str,
             conversation_id: str = None, stream: bool = False) -> Dict:
        """
        与智能体对话（调用真实 LLM）

        如果智能体绑定了 RAG 技能，会先从知识库检索相关文档，
        再将检索结果注入上下文，最后由 LLM 生成回答。
        """
        agent = _agent_registry.get(agent_id)
        if not agent:
            return {"content": f"[错误] 智能体 {agent_id} 不存在"}

        # --- 构建消息列表 ---
        messages: List[BaseMessage] = [SystemMessage(content=agent["system_prompt"])]

        # RAG 检索：从绑定的知识库中检索相关文档
        rag_context = ""
        if agent["rag_kb_ids"]:
            top_k = agent["rag_config"].get("retrieval_top_k", 3)
            for kb_id in agent["rag_kb_ids"]:
                kb = _kb_registry.get(kb_id)
                if kb and kb["vectorstore"]:
                    docs = kb["vectorstore"].similarity_search(message, k=top_k)
                    if docs:
                        rag_context += "\n\n---\n".join(d.page_content for d in docs)

            if rag_context:
                rag_template = agent["rag_config"].get("prompt_template",
                    "基于以下参考资料回答用户问题。如果资料中没有相关信息，请明确说明。\n\n"
                    "参考资料：\n{context}")
                messages.append(SystemMessage(content=rag_context))

        # 对话历史（保留最近 6 条消息 = 3 轮对话）
        for h in agent["history"][-6:]:
            messages.append(h)

        # 当前用户消息
        messages.append(HumanMessage(content=message))

        # --- 调用 LLM ---
        try:
            response = self.llm.invoke(messages)
            content = response.content
        except Exception as e:
            content = f"[LLM 调用失败] {e}"

        # --- 更新对话历史 ---
        agent["history"].append(HumanMessage(content=message))
        agent["history"].append(AIMessage(content=content))

        return {"content": content}

    def chat_multi_turn(self, agent_id: str, messages: List[Dict]) -> Dict:
        """多轮对话（传入历史消息列表）"""
        agent = _agent_registry.get(agent_id)
        if not agent:
            return {"content": f"[错误] 智能体 {agent_id} 不存在"}

        lc_messages: List[BaseMessage] = [SystemMessage(content=agent["system_prompt"])]
        for m in messages:
            role = m.get("role", "user")
            if role == "user":
                lc_messages.append(HumanMessage(content=m["content"]))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=m["content"]))
            elif role == "system":
                lc_messages.append(SystemMessage(content=m["content"]))

        response = self.llm.invoke(lc_messages)
        return {"content": response.content}

    # ========== 知识库（FAISS 向量存储）==========

    def create_knowledge_base(self, name: str, description: str = "",
                              embedding_model: str = "default") -> Dict:
        """创建知识库（使用 FAISS 向量存储）"""
        kb_id = _gen_id("kb")
        _kb_registry[kb_id] = {
            "id": kb_id,
            "name": name,
            "description": description,
            "embeddings": _create_embeddings(),
            "vectorstore": None,  # 首次上传文档时创建
            "chunk_size": 500,
            "chunk_overlap": 50,
        }
        return {"id": kb_id, "name": name}

    def upload_text(self, kb_id: str, title: str, content: str,
                    chunk_size: int = 500) -> Dict:
        """
        上传文本到知识库
        文本会被分块 → 嵌入 → 存入 FAISS 索引
        """
        kb = _kb_registry.get(kb_id)
        if not kb:
            return {"error": f"知识库 {kb_id} 不存在"}

        # 更新分块参数
        kb["chunk_size"] = chunk_size
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=min(50, chunk_size // 10),
        )

        # 分块
        chunks = splitter.split_text(content)
        texts = [f"标题：{title}\n{chunk}" for chunk in chunks]

        # 嵌入并存入 FAISS
        if kb["vectorstore"] is None:
            kb["vectorstore"] = FAISS.from_texts(texts, kb["embeddings"])
        else:
            kb["vectorstore"].add_texts(texts)

        return {"status": "ok", "title": title, "chunks": len(chunks)}

    def query_knowledge_base(self, kb_id: str, query: str, top_k: int = 5) -> Dict:
        """检索知识库（向量相似度搜索）"""
        kb = _kb_registry.get(kb_id)
        if not kb or kb["vectorstore"] is None:
            return {"results": []}

        docs = kb["vectorstore"].similarity_search(query, k=top_k)
        return {"results": [{"content": d.page_content, "score": 0} for d in docs]}

    # ========== 技能管理 ==========

    def create_skill(self, name: str, skill_type: str, config: Dict) -> Dict:
        """创建技能（RAG 类型会绑定知识库）"""
        skill_id = _gen_id("skill")
        _skill_registry[skill_id] = {
            "id": skill_id,
            "name": name,
            "type": skill_type,
            "config": config,
        }
        return {"id": skill_id, "name": name}

    def bind_skill_to_agent(self, agent_id: str, skill_id: str) -> Dict:
        """将技能绑定到智能体（RAG 技能会启用知识库检索）"""
        agent = _agent_registry.get(agent_id)
        skill = _skill_registry.get(skill_id)
        if not agent or not skill:
            return {"error": "智能体或技能不存在"}

        if skill["type"] == "rag":
            kb_id = skill["config"].get("knowledge_base_id")
            if kb_id and kb_id in _kb_registry:
                agent["rag_kb_ids"].append(kb_id)
                agent["rag_config"] = skill["config"]

        # 记录技能元信息
        agent["skills_meta"].append({
            "skill_id": skill_id,
            "name": skill["name"],
            "type": skill["type"],
        })
        return {"status": "ok"}

    # ========== 工作流（多智能体编排）==========

    def create_workflow(self, name: str, description: str, steps: List[Dict]) -> Dict:
        """创建多智能体工作流"""
        wf_id = _gen_id("workflow")
        _workflow_registry[wf_id] = {
            "id": wf_id,
            "name": name,
            "description": description,
            "steps": steps,
        }
        return {"id": wf_id, "name": name}

    def run_workflow(self, workflow_id: str, input_data: Dict) -> Dict:
        """
        运行工作流

        按步骤顺序执行，支持：
        - 变量模板替换 ${variable}
        - 条件分支（condition 字段）
        - 并行步骤（parallel_with 字段，简化为串行）
        """
        wf = _workflow_registry.get(workflow_id)
        if not wf:
            return {"error": f"工作流 {workflow_id} 不存在"}

        results: Dict[str, Any] = {}
        for step in wf["steps"]:
            step_name = step.get("name", f"步骤{step.get('step', '?')}")
            agent_id = step.get("agent_id")

            # 条件分支检查
            condition = step.get("condition")
            if condition:
                # 简化条件判断：检查前一步结果中是否包含特定值
                if not self._check_condition(condition, input_data, results):
                    print(f"  ⏭ 跳过步骤「{step_name}」（条件不满足）")
                    results[step.get("output", step_name)] = {"content": "[跳过]"}
                    continue

            # 解析输入模板
            step_input = step.get("input", "${user_message}")
            resolved_input = self._resolve_template(step_input, input_data, results)

            print(f"  ▶ 执行步骤「{step_name}」...")

            # 调用智能体
            if agent_id and agent_id in _agent_registry:
                result = self.chat(agent_id, resolved_input)
            else:
                result = {"content": f"[智能体 {agent_id} 不存在]"}

            output_key = step.get("output", step_name)
            results[output_key] = result

        return results

    @staticmethod
    def _resolve_template(template, input_data: Dict, results: Dict) -> str:
        """解析 ${variable} 模板变量"""
        if isinstance(template, dict):
            template = json.dumps(template, ensure_ascii=False)

        # 替换 input_data 变量
        for key, val in input_data.items():
            template = template.replace(f"${{{key}}}", str(val))

        # 替换前序步骤结果变量
        for key, val in results.items():
            if isinstance(val, dict):
                val_str = val.get("content", json.dumps(val, ensure_ascii=False))
            else:
                val_str = str(val)
            template = template.replace(f"${{{key}}}", val_str)

        return template

    @staticmethod
    def _check_condition(condition: str, input_data: Dict, results: Dict) -> bool:
        """简化条件判断"""
        # 格式: ${variable} == 'value'
        if "==" in condition:
            left, right = condition.split("==", 1)
            left = left.strip().replace("${", "").replace("}", "")
            right = right.strip().strip("'\"")

            # 在 input_data 和 results 中查找变量值
            actual = ""
            if left in input_data:
                actual = str(input_data[left])
            elif left in results:
                val = results[left]
                if isinstance(val, dict):
                    actual = val.get("content", "")
                else:
                    actual = str(val)

            return right in actual or actual == right
        return True

    # ========== 工具调用 ==========

    def call_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """调用工具（简化实现，返回模拟结果）"""
        return {"tool": tool_name, "parameters": parameters, "result": "[模拟工具调用]"}


# ============================================================
#  便捷函数
# ============================================================

_client_instance: Optional[TeleAgentClient] = None


def get_client() -> TeleAgentClient:
    """获取默认客户端实例（单例）"""
    global _client_instance
    if _client_instance is None:
        _client_instance = TeleAgentClient()
    return _client_instance


def quick_chat(agent_id: str, message: str) -> str:
    """快捷对话，返回文本内容"""
    client = get_client()
    result = client.chat(agent_id, message)
    return result.get("content", "")


def reset_registry():
    """重置所有注册表（调试用）"""
    global _client_instance
    _agent_registry.clear()
    _kb_registry.clear()
    _skill_registry.clear()
    _workflow_registry.clear()
    _counters.update({"agent": 0, "kb": 0, "skill": 0, "workflow": 0})
    _client_instance = None


# ============================================================
#  测试入口
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("LangChain LLM 客户端 - 连接测试")
    print("=" * 50)
    print(f"  API 地址: {LLM_BASE_URL or '(未配置)'}")
    print(f"  模型名称: {LLM_MODEL}")
    print(f"  嵌入模型: {EMBEDDING_MODEL}")
    print(f"  API Key:  {'已配置' if LLM_API_KEY else '未配置'}")
    print()

    if not check_config():
        print("\n请先配置 .env 文件！")
        raise SystemExit(1)

    try:
        client = get_client()
        # 简单对话测试
        agent = client.create_agent(
            name="测试助手",
            description="连接测试",
            system_prompt="你是一个友好的助手，请简短回答。"
        )
        result = client.chat(agent["id"], "你好，请用一句话介绍你自己。")
        print(f"\n测试对话结果:\n  {result['content']}")
        print("\n连接成功！LLM 客户端工作正常。")
    except Exception as e:
        print(f"\n连接失败: {e}")
        print("请检查 .env 配置和网络连接。")
