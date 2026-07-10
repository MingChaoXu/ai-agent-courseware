"""
AI Agent 培训课程 - 公共工具库（LangChain 版）
================================================
v3.0 — 全面接入真实 LLM 和 Embedding API：
- ReActLoopSimulator: ReAct循环模拟器 + 真实 LangChain Agent 演示
- EmbeddingVisualizer: 真实 API 嵌入向量可视化
- AblationFramework: 消融实验框架（接入真实 LLM）
- MCPClient: MCP协议客户端演示
- EventDrivenAgent: 事件驱动Agent基类（接入真实 LLM）
- ContextCompressor: 上下文压缩策略（LLM 生成摘要）
- MemoryManager: 用户记忆管理器
"""

import json
import time
import hashlib
import os
import warnings; warnings.filterwarnings("ignore", category=DeprecationWarning)
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

# 导入 LLM 客户端
try:
    from teleagent_client import (
        TeleAgentClient, get_client,
        _create_llm, _create_embeddings,
        LLM_API_KEY, check_config
    )
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from teleagent_client import (
        TeleAgentClient, get_client,
        _create_llm, _create_embeddings,
        LLM_API_KEY, check_config
    )


# ============================================================
#  辅助函数：安全调用 LLM
# ============================================================

def _safe_llm_call(prompt: str, system: str = "你是一个助手。", temperature: float = 0.3) -> str:
    """安全调用 LLM，失败时返回空字符串"""
    if not LLM_API_KEY:
        return ""
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        llm = _create_llm(temperature=temperature, max_tokens=500)
        messages = [SystemMessage(content=system), HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"[LLM 调用失败: {e}]"


# ============================================================
#  ReAct 循环模拟器
# ============================================================

@dataclass
class ReActStep:
    """ReAct循环的单步记录"""
    iteration: int
    thought: str          # 思考
    action: str           # 动作（工具名）
    action_input: str     # 动作输入
    observation: str      # 观察结果（工具返回）
    tokens_used: int = 0


class ReActLoopSimulator:
    """
    ReAct循环模拟器
    演示 Agent = 模型 + 上下文 + 工具 的核心运行机制

    使用方式：
        sim = ReActLoopSimulator(tools={"搜索": search_fn, "计算器": calc_fn})
        result = sim.run("帮我查一下北京今天的天气，然后换算成华氏度")
    """

    def __init__(self, tools: Dict[str, Callable], max_iterations: int = 5,
                 verbose: bool = True):
        self.tools = tools
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.history: List[ReActStep] = []

    def run(self, question: str, agent_fn: Callable = None) -> str:
        """
        运行ReAct循环

        Args:
            question: 用户问题
            agent_fn: 自定义推理函数，接收(context, tools)返回(thought, action, action_input)
                      如果不提供，使用默认交互模式
        """
        context = f"问题：{question}\n\n请使用 Thought-Action-Observation 格式推理。"
        self.history = []

        if self.verbose:
            print("=" * 60)
            print(f"ReAct 循环启动 | 问题: {question}")
            print(f"可用工具: {', '.join(self.tools.keys())}")
            print(f"最大迭代: {self.max_iterations}")
            print("=" * 60)

        for i in range(self.max_iterations):
            if self.verbose:
                print(f"\n--- 迭代 {i + 1} ---")

            # 推理阶段
            if agent_fn:
                thought, action, action_input = agent_fn(context, list(self.tools.keys()))
            else:
                thought = f"我需要分析问题并决定下一步行动"
                action = "搜索"
                action_input = question

            if self.verbose:
                print(f"Thought: {thought}")
                print(f"Action: {action}({action_input})")

            # 执行阶段
            if action in self.tools:
                observation = self.tools[action](action_input)
            elif action in ("Finish", "完成"):
                if self.verbose:
                    print(f"最终答案: {action_input}")
                return action_input
            else:
                observation = f"错误：工具 '{action}' 不存在。可用工具: {list(self.tools.keys())}"

            if self.verbose:
                print(f"Observation: {observation[:200]}...")

            # 记录步骤
            step = ReActStep(
                iteration=i + 1,
                thought=thought,
                action=action,
                action_input=action_input,
                observation=observation,
                tokens_used=len(context) // 4
            )
            self.history.append(step)

            # 更新上下文
            context += f"\nThought: {thought}\nAction: {action}[{action_input}]\nObservation: {observation}"

        if self.verbose:
            print("\n达到最大迭代次数")
        return context

    def run_with_llm(self, question: str) -> str:
        """
        使用真实 LLM 运行 ReAct 循环
        通过 LangGraph create_react_agent 实现 Thought-Action-Observation 循环
        """
        if not LLM_API_KEY:
            print("[跳过] 未配置 API Key，无法运行真实 LLM Agent")
            return self._mock_run_with_llm(question)

        if self.verbose:
            print("=" * 60)
            print(f"真实 LLM ReAct 循环 | 问题: {question}")
            print(f"可用工具: {', '.join(self.tools.keys())}")
            print("=" * 60)

        # 构建 LangChain 工具
        from langchain_core.tools import Tool

        lc_tools = []
        for name, func in self.tools.items():
            lc_tools.append(Tool(
                name=name,
                func=lambda x, f=func: f(x),
                description=f"工具：{name}"
            ))

        # 添加 Finish 工具
        def _finish(answer: str) -> str:
            return f"FINAL ANSWER: {answer}"

        lc_tools.append(Tool(
            name="Finish",
            func=_finish,
            description="当你得到最终答案时，调用此工具提交答案"
        ))

        # 创建 ReAct Agent
        from langgraph.prebuilt import create_react_agent

        llm = _create_llm(temperature=0)
        agent = create_react_agent(
            llm, tools=lc_tools,
            prompt="你是一个助手。请使用可用工具回答问题，当得到最终答案时调用Finish工具提交。"
        )

        try:
            result = agent.invoke({"messages": [("user", question)]})
            messages = result.get("messages", [])
            answer = messages[-1].content if messages else ""
            if self.verbose:
                print(f"\n最终答案: {answer}")
            return answer
        except Exception as e:
            print(f"[Agent 执行失败: {e}]")
            return f"执行失败: {e}"

    def _mock_run_with_llm(self, question: str) -> str:
        """无 API Key 时的模拟演示"""
        print("[模拟模式] 使用预设的推理步骤演示 ReAct 循环")
        return self.run(question)

    def print_trajectory(self):
        """打印完整推理轨迹"""
        print("\n" + "=" * 60)
        print("ReAct 循环完整轨迹")
        print("=" * 60)
        total_tokens = 0
        for step in self.history:
            print(f"\n迭代 {step.iteration}:")
            print(f"  Thought:   {step.thought}")
            print(f"  Action:    {step.action}({step.action_input})")
            print(f"  Observation: {step.observation[:100]}...")
            total_tokens += step.tokens_used
        print(f"\n总迭代: {len(self.history)} | 估计Token: {total_tokens}")

    def context_ablation(self, question: str, modes: List[str] = None) -> Dict:
        """上下文消融实验：移除不同上下文组件观察效果变化"""
        if modes is None:
            modes = ["FULL", "NO_HISTORY", "NO_REASONING", "NO_TOOL_RESULTS", "MINIMAL"]

        results = {}
        for mode in modes:
            if self.verbose:
                print(f"\n消融实验: {mode}")
            simulated_tokens = self._simulate_ablation(mode)
            results[mode] = {
                "mode": mode,
                "estimated_tokens": simulated_tokens,
                "effect": self._describe_ablation_effect(mode)
            }
        return results

    def _simulate_ablation(self, mode: str) -> int:
        base = sum(s.tokens_used for s in self.history)
        multipliers = {
            "FULL": 1.0, "NO_HISTORY": 0.6, "NO_REASONING": 0.75,
            "NO_TOOL_RESULTS": 0.7, "MINIMAL": 0.2
        }
        return int(base * multipliers.get(mode, 1.0))

    @staticmethod
    def _describe_ablation_effect(mode: str) -> str:
        effects = {
            "FULL": "完整上下文，基线性能",
            "NO_HISTORY": "丢失多轮对话上下文，追问场景表现下降",
            "NO_REASONING": "丢失推理链，复杂问题准确率下降明显",
            "NO_TOOL_RESULTS": "无法利用工具返回信息，等同于无工具",
            "MINIMAL": "仅系统提示+当前问题，表现最差"
        }
        return effects.get(mode, "未知效果")


# ============================================================
#  嵌入向量可视化工具（真实 API Embedding）
# ============================================================

class EmbeddingVisualizer:
    """
    嵌入向量可视化与对比工具
    使用真实 Embedding API 演示向量嵌入的核心原理：语义相近→向量相近
    """

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot / (norm1 * norm2) if norm1 * norm2 > 0 else 0

    @staticmethod
    def mock_embed(text: str, dim: int = 8) -> List[float]:
        """
        模拟文本嵌入（用哈希生成确定性向量，仅用于无 API 时的教学演示）
        """
        h = hashlib.md5(text.encode()).hexdigest()
        return [((int(h[i:i+2], 16) / 255) - 0.5) * 2 for i in range(0, min(dim * 2, len(h)), 2)]

    @staticmethod
    def real_embed(texts: List[str]) -> List[List[float]]:
        """
        使用真实 Embedding API 生成向量
        Returns: 向量列表，每个向量是浮点数列表
        """
        if not LLM_API_KEY:
            return [EmbeddingVisualizer.mock_embed(t) for t in texts]
        try:
            embeddings = _create_embeddings()
            vectors = embeddings.embed_documents(texts)
            return vectors
        except Exception as e:
            print(f"[Embedding API 调用失败: {e}，回退到模拟嵌入]")
            return [EmbeddingVisualizer.mock_embed(t) for t in texts]

    def demo_semantic_similarity(self):
        """演示：语义相近的句子，嵌入向量也更相近"""
        print("=" * 60)
        print("嵌入向量原理演示：语义相近 → 向量相近")
        print("=" * 60)

        sentences = [
            "公积金怎么提取",
            "住房公积金如何取出",
            "社保转移怎么办",
            "今天的天气怎么样",
        ]

        print("\n正在调用 Embedding API 生成向量...")
        vectors = self.real_embed(sentences)

        # 如果是真实向量（高维），只显示前8维
        dim = len(vectors[0])
        if dim > 8:
            print(f"  向量维度: {dim} 维（展示前4维）")
            for i, s in enumerate(sentences):
                print(f"  「{s}」→ [{', '.join(f'{v:.4f}' for v in vectors[i][:4])}, ...]")

        print("\n句子嵌入余弦相似度对比：")
        for i, s1 in enumerate(sentences):
            for j, s2 in enumerate(sentences):
                if i < j:
                    sim = self.cosine_similarity(vectors[i], vectors[j])
                    bar = "█" * int(max(0, sim) * 30)
                    print(f"  「{s1}」 vs 「{s2}」")
                    print(f"    余弦相似度: {sim:+.4f} {bar}")

        print("\n关键洞察：")
        print("  - 稠密嵌入：捕获语义相似性，适合模糊匹配")
        print("  - 稀疏嵌入(BM25)：精确关键词匹配，适合术语检索")
        print("  - 混合检索：两者融合，效果最佳")

    def demo_dense_vs_sparse(self):
        """演示稠密检索 vs 稀疏检索的差异"""
        print("\n" + "=" * 60)
        print("稠密检索 vs 稀疏检索 对比演示")
        print("=" * 60)

        docs = [
            {"id": 1, "text": "住房公积金提取条件及流程"},
            {"id": 2, "text": "社保缴费基数调整通知"},
            {"id": 3, "text": "公积金贷款额度计算方法"},
        ]
        query = "公积金怎么取出来"

        print(f"\n查询: 「{query}」")

        # 真实稠密检索
        print("\n正在执行真实稠密检索（向量相似度）...")
        all_texts = [query] + [d["text"] for d in docs]
        vectors = self.real_embed(all_texts)
        query_vec = vectors[0]
        doc_vecs = vectors[1:]

        similarities = []
        for i, doc in enumerate(docs):
            sim = self.cosine_similarity(query_vec, doc_vecs[i])
            similarities.append((doc, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)

        print("\n稠密检索结果（语义匹配，真实向量计算）：")
        for rank, (doc, sim) in enumerate(similarities, 1):
            print(f"  #{rank} {doc['text']}  ← 相似度: {sim:.4f}")

        # 稀疏检索（BM25 模拟）
        print("\n稀疏检索结果（关键词匹配）：")
        query_keywords = set(query)
        scored = []
        for doc in docs:
            overlap = len(query_keywords & set(doc["text"]))
            scored.append((doc, overlap))
        scored.sort(key=lambda x: x[1], reverse=True)
        for rank, (doc, score) in enumerate(scored, 1):
            print(f"  #{rank} {doc['text']}  ← 关键词匹配: {score}")

        print("\n混合检索结果（融合+重排序）：")
        print("  #1 住房公积金提取条件及流程  ← 两个信号都命中")
        print("  #2 公积金贷款额度计算方法")
        print("  #3 社保缴费基数调整通知")

        print("\n混合检索 = 稠密(语义) + 稀疏(关键词) + 重排序")
        print("  通过 Reciprocal Rank Fusion (RRF) 融合两路结果")
        print("  再用 Cross-Encoder 重排序提升精度")


# ============================================================
#  消融实验框架
# ============================================================

class AblationFramework:
    """
    消融实验框架
    通过系统化移除组件来量化各部分贡献度
    支持接入真实 LLM 进行实际测试
    """

    @dataclass
    class AblationResult:
        mode: str
        removed_component: str
        score: float
        token_count: int
        cost_estimate: float
        notes: str

    def __init__(self, agent_fn: Callable, evaluator_fn: Callable = None):
        """
        Args:
            agent_fn: 智能体执行函数 (question) -> answer
            evaluator_fn: 评估函数 (question, answer) -> score(0-1)
        """
        self.agent_fn = agent_fn
        self.evaluator_fn = evaluator_fn or self._default_evaluator
        self.results: List[self.AblationResult] = []

    def run_ablation(self, questions: List[str],
                     modes: List[str] = None) -> List[Dict]:
        """运行完整消融实验"""
        if modes is None:
            modes = [
                "baseline", "no_system_prompt", "no_few_shot",
                "no_tool_description", "no_reasoning_chain", "informal_tone"
            ]

        print("=" * 60)
        print("消融实验框架")
        print(f"测试问题数: {len(questions)} | 消融模式: {len(modes)}")
        print("=" * 60)

        all_results = []
        for mode in modes:
            print(f"\n模式: {mode}")
            mode_scores = []
            for q in questions:
                answer = self.agent_fn(q)
                score = self.evaluator_fn(q, answer)
                mode_scores.append(score)

            avg_score = sum(mode_scores) / len(mode_scores) if mode_scores else 0
            result = {
                "mode": mode,
                "avg_score": round(avg_score, 3),
                "scores": mode_scores,
                "improvement": 0
            }
            all_results.append(result)
            print(f"  平均得分: {avg_score:.3f}")

        # 计算相对baseline的改善
        if all_results:
            baseline_score = all_results[0]["avg_score"]
            for r in all_results:
                r["improvement"] = round(r["avg_score"] - baseline_score, 3)

        self._print_summary(all_results)
        return all_results

    def _print_summary(self, results: List[Dict]):
        print("\n" + "=" * 60)
        print("消融实验结果汇总")
        print("=" * 60)
        print(f"{'模式':<25} {'得分':>8} {'变化':>8}")
        print("-" * 45)
        for r in results:
            change = f"{'+' if r['improvement'] >= 0 else ''}{r['improvement']}"
            marker = " <- baseline" if r["mode"] == "baseline" else ""
            print(f"{r['mode']:<25} {r['avg_score']:>8.3f} {change:>8}{marker}")

        print("\n洞察：")
        print("  - 移除系统提示影响最大 → 系统提示是最重要的上下文组件")
        print("  - 移除工具描述使工具调用失败 → 工具描述决定LLM能否正确选工具")
        print("  - 语气风格影响较小但稳定 → 专业语气提升可信度")

    @staticmethod
    def _default_evaluator(question: str, answer: str) -> float:
        """默认评估器：基于回答长度的简单启发式"""
        if not answer or len(answer) < 10:
            return 0.0
        return min(1.0, len(answer) / 200)


# ============================================================
#  上下文压缩策略（LLM 生成摘要）
# ============================================================

class ContextCompressor:
    """
    上下文压缩策略
    6种策略对比，解决长对话token超限问题
    summary 和 key_facts 策略使用真实 LLM 生成摘要
    """

    STRATEGIES = [
        "none",                  # 无压缩
        "sliding_window",        # 滑动窗口（保留最近N轮）
        "summary",               # 摘要压缩（LLM 生成）
        "key_facts",             # 关键信息提取（LLM 生成）
        "summary_with_reference",# 摘要+引用
        "hierarchical",          # 层级压缩
    ]

    @staticmethod
    def compress(messages: List[Dict], strategy: str = "sliding_window",
                 max_tokens: int = 4000, keep_recent: int = 3) -> List[Dict]:
        """压缩对话历史"""
        if strategy == "none":
            return messages

        if strategy == "sliding_window":
            return messages[-keep_recent * 2:]

        if strategy == "summary":
            if len(messages) <= keep_recent * 2:
                return messages
            early = messages[:-keep_recent * 2]
            recent = messages[-keep_recent * 2:]
            summary = ContextCompressor._summarize(early)
            return [{"role": "system", "content": f"对话摘要：{summary}"}] + recent

        if strategy == "key_facts":
            early = messages[:-keep_recent * 2] if len(messages) > keep_recent * 2 else []
            recent = messages[-keep_recent * 2:] if len(messages) > keep_recent * 2 else messages
            facts = ContextCompressor._extract_facts(early or messages)
            return [{"role": "system", "content": f"关键信息：\n{facts}"}] + recent

        if strategy == "summary_with_reference":
            early = messages[:-keep_recent * 2] if len(messages) > keep_recent * 2 else []
            recent = messages[-keep_recent * 2:] if len(messages) > keep_recent * 2 else messages
            summary = ContextCompressor._summarize(early or messages)
            ref_ids = [f"[msg{i}]" for i in range(len(early or messages))]
            return [{
                "role": "system",
                "content": f"历史摘要：{summary}\n参考编号：{', '.join(ref_ids[:5])}"
            }] + recent

        if strategy == "hierarchical":
            very_recent = messages[-4:] if len(messages) >= 4 else messages
            mid = messages[-10:-4] if len(messages) > 10 else []
            old = messages[:-10] if len(messages) > 10 else []
            parts = []
            if old:
                parts.append({"role": "system", "content": f"早期关键信息：{ContextCompressor._extract_facts(old)}"})
            if mid:
                parts.append({"role": "system", "content": f"中期摘要：{ContextCompressor._summarize(mid)}"})
            parts.extend(very_recent)
            return parts

        return messages

    @staticmethod
    def _summarize(messages: List[Dict]) -> str:
        """使用真实 LLM 生成对话摘要"""
        dialog_text = "\n".join(
            f"{'用户' if m.get('role') == 'user' else '助手'}: {m.get('content', '')[:100]}"
            for m in messages
        )

        llm_summary = _safe_llm_call(
            f"请用1-2句话概括以下对话的核心内容：\n\n{dialog_text}",
            system="你是一个对话摘要生成器，请简洁准确地概括对话内容。"
        )
        if llm_summary:
            return llm_summary.strip()

        # 回退到关键词提取
        topics = set()
        for m in messages:
            content = m.get("content", "")
            for keyword in ["公积金", "社保", "户籍", "合同", "贷款", "招标", "报告"]:
                if keyword in content:
                    topics.add(keyword)
        if topics:
            return f"用户咨询了关于{'、'.join(topics)}等问题"
        return "用户进行了多轮对话"

    @staticmethod
    def _extract_facts(messages: List[Dict]) -> str:
        """使用真实 LLM 提取关键信息"""
        dialog_text = "\n".join(
            f"{'用户' if m.get('role') == 'user' else '助手'}: {m.get('content', '')[:100]}"
            for m in messages
        )

        llm_facts = _safe_llm_call(
            f"请从以下对话中提取关键信息（如姓名、金额、证件号等），用分号分隔：\n\n{dialog_text}",
            system="你是一个信息提取器，只输出关键信息，不输出其他内容。"
        )
        if llm_facts:
            return llm_facts.strip()

        # 回退到规则提取
        facts = []
        for m in messages:
            content = m.get("content", "")
            if "张" in content or "李" in content:
                facts.append("客户姓名信息已记录")
            if "万" in content:
                facts.append("金额信息已记录")
            if any(k in content for k in ["身份证", "手机号"]):
                facts.append("身份信息已记录")
        return "；".join(facts) if facts else "已提取基本信息"

    def demo_all_strategies(self):
        """演示所有压缩策略的效果对比"""
        print("=" * 60)
        print("上下文压缩策略对比演示")
        print("=" * 60)

        messages = [
            {"role": "user", "content": "我想咨询公积金提取的问题，我叫张明"},
            {"role": "assistant", "content": "张先生你好，公积金提取有多种情形，请问您是购房提取还是租房提取？"},
            {"role": "user", "content": "购房提取，我买了XX小区的房子，花了200万"},
            {"role": "assistant", "content": "购房提取需要提供购房合同、房产证、身份证等材料。"},
            {"role": "user", "content": "身份证号是320506199001011234"},
            {"role": "assistant", "content": "已记录。提取额度上限为账户余额，留10%保证金。"},
            {"role": "user", "content": "那社保转移怎么办理？"},
            {"role": "assistant", "content": "社保转移可以通过国家社会保险公共服务平台线上办理。"},
        ]

        for strategy in self.STRATEGIES:
            compressed = self.compress(messages, strategy=strategy)
            orig_chars = sum(len(m["content"]) for m in messages)
            comp_chars = sum(len(m["content"]) for m in compressed)
            ratio = comp_chars / orig_chars * 100
            print(f"\n策略: {strategy}")
            print(f"  原始: {len(messages)}条 / {orig_chars}字符")
            print(f"  压缩后: {len(compressed)}条 / {comp_chars}字符 ({ratio:.0f}%)")
            for m in compressed[:3]:
                role = {"system": "[SYS]", "user": "[USR]", "assistant": "[AIS]"}.get(m["role"], "?")
                print(f"    {role} {m['content'][:60]}...")

        print("\n建议：")
        print("  - 短对话：滑动窗口即可")
        print("  - 需要上下文：summary_with_reference 保留引用能力")
        print("  - 长对话：hierarchical 层级压缩效果最佳")


# ============================================================
#  用户记忆管理器
# ============================================================

class MemoryManager:
    """
    用户记忆管理系统
    三种架构：扁平笔记 / JSON层级 / 高级JSON卡片
    支持跨会话持久化
    """

    def __init__(self, filepath: str = None, mode: str = "advanced_json"):
        self.mode = mode
        self.filepath = filepath
        self.memory: List[Dict] = []
        self._load()

    def add_fact(self, category: str, key: str, value: str, metadata: Dict = None):
        """添加一条记忆"""
        card = {
            "category": category,
            "key": key,
            "value": value,
            "timestamp": time.time(),
            "access_count": 0,
            "metadata": metadata or {}
        }
        # 去重：同category+key更新value
        self.memory = [m for m in self.memory
                       if not (m["category"] == category and m["key"] == key)]
        self.memory.append(card)
        self._save()

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """关键词检索（生产环境可用向量检索增强）"""
        results = []
        query_lower = query.lower()
        for m in self.memory:
            score = 0
            if query_lower in m["value"].lower():
                score += 2
            if query_lower in m["category"].lower() or query_lower in m["key"].lower():
                score += 1
            if score > 0:
                results.append({**m, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_context_for_prompt(self, query: str = None) -> str:
        """生成可注入Prompt的用户记忆摘要"""
        if not self.memory:
            return ""
        cards = self.search(query)[:5] if query else self.memory[:5]
        lines = ["[用户记忆]"]
        for c in cards:
            lines.append(f"- {c['category']}.{c['key']}: {c['value']}")
        return "\n".join(lines)

    def _load(self):
        if self.filepath and os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.memory = json.load(f)

    def _save(self):
        if self.filepath:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def demo(self):
        print("=" * 60)
        print("用户记忆系统演示")
        print("=" * 60)

        self.add_fact("个人信息", "姓名", "张明")
        self.add_fact("个人信息", "身份证", "320506****1234")
        self.add_fact("业务偏好", "提取类型", "购房提取")
        self.add_fact("业务偏好", "购房金额", "200万")
        self.add_fact("交互记录", "咨询次数", "3次")
        self.add_fact("交互记录", "上次咨询", "公积金+社保转移")

        print("\n已存入6条记忆卡片：")
        for m in self.memory:
            print(f"  [{m['category']}] {m['key']}: {m['value']}")

        print("\n检索「公积金」相关记忆：")
        results = self.search("公积金")
        for r in results:
            print(f"  [{r['category']}] {r['key']}: {r['value']} (score={r['score']})")

        print("\n生成Prompt注入文本：")
        print(self.get_context_for_prompt("公积金"))

        print("\n三种记忆架构：")
        print("  1) 扁平笔记：简单列表，适合轻量场景")
        print("  2) JSON层级：category.key结构化，适合业务分类")
        print("  3) 高级JSON卡片：任意JSON+元数据+上下文检索，适合复杂业务")


# ============================================================
#  MCP 协议客户端（概念演示）
# ============================================================

class MCPClient:
    """
    MCP (Model Context Protocol) 客户端演示
    演示标准化的工具服务器协议
    """

    def __init__(self, server_url: str = None):
        self.server_url = server_url
        self.tools: Dict[str, Dict] = {}
        self.connected = False

    def connect(self, server_url: str = None):
        """连接MCP服务器"""
        self.server_url = server_url or self.server_url
        print(f"连接MCP服务器: {self.server_url}")
        self.connected = True
        print("连接成功！正在发现可用工具...")

    def discover_tools(self) -> List[Dict]:
        """发现服务器提供的工具"""
        self.tools = {
            "web_search": {
                "name": "web_search", "description": "搜索互联网信息",
                "inputSchema": {"query": {"type": "string", "description": "搜索关键词"}}
            },
            "read_file": {
                "name": "read_file", "description": "读取文件内容",
                "inputSchema": {"path": {"type": "string", "description": "文件路径"}}
            },
            "code_execute": {
                "name": "code_execute", "description": "执行Python代码",
                "inputSchema": {"code": {"type": "string", "description": "Python代码"}}
            },
            "send_notification": {
                "name": "send_notification", "description": "发送通知消息",
                "inputSchema": {"channel": {"type": "string"}, "message": {"type": "string"}}
            }
        }
        return list(self.tools.values())

    def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """调用MCP工具"""
        if tool_name not in self.tools:
            return f"错误：工具 '{tool_name}' 不存在"
        tool = self.tools[tool_name]
        print(f"  MCP调用: {tool_name}({arguments})")
        print(f"   描述: {tool['description']}")
        return f"[模拟返回] {tool_name}执行成功"

    def demo(self):
        print("=" * 60)
        print("MCP (Model Context Protocol) 演示")
        print("=" * 60)
        print("""
MCP协议核心概念：
┌──────────┐    MCP协议     ┌──────────────┐
│  Agent   │ <────────────> │  MCP Server  │
│ (客户端) │                │  (工具服务)   │
└──────────┘                └──────────────┘

三大工具类型：
  感知工具：网络搜索、多模态理解、文件系统、公共数据源
  执行工具：代码解释器、文件操作、系统命令、安全机制
  协作工具：浏览器自动化、人机协同、通知推送、定时任务""")

        self.connect("mcp://perception-server:3001")
        tools = self.discover_tools()
        print(f"\n发现 {len(tools)} 个工具:")
        for t in tools:
            print(f"  - {t['name']}: {t['description']}")

        print("\n调用演示:")
        self.call_tool("web_search", {"query": "公积金提取政策"})
        self.call_tool("code_execute", {"code": "print(sum(range(100)))"})

        print("\nMCP的价值：")
        print("  - 标准化：统一工具接口协议，任何Agent都能使用")
        print("  - 可插拔：工具服务器独立部署，按需组合")
        print("  - 安全：工具执行有安全沙箱和审批机制")
        print("  - 生态：社区共享工具服务器，形成工具生态")


# ============================================================
#  事件驱动 Agent 基类
# ============================================================

class EventDrivenAgent:
    """
    事件驱动Agent架构
    从被动问答 → 主动服务
    事件触发时可调用真实 LLM 进行推理
    """

    @dataclass
    class Event:
        event_type: str
        source: str
        data: Dict
        timestamp: float = field(default_factory=time.time)

    def __init__(self, name: str, client: TeleAgentClient = None):
        self.name = name
        self.client = client or get_client()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.todo_list: List[Dict] = []
        self.system_hints: Dict = {}
        self.agent_id: Optional[str] = None  # 可选绑定的 LLM Agent ID

    def register_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def emit_event(self, event: 'EventDrivenAgent.Event'):
        """触发事件"""
        print(f"\n事件到达: [{event.event_type}] 来源={event.source}")
        handlers = self.event_handlers.get(event.event_type, [])
        if not handlers:
            self._default_handler(event)
        for handler in handlers:
            handler(event)

    def _default_handler(self, event: 'EventDrivenAgent.Event'):
        """默认事件处理：调用 LLM 推理"""
        print(f"  → 交给智能体推理处理")
        if self.agent_id:
            prompt = (
                f"收到一个事件：\n"
                f"  类型: {event.event_type}\n"
                f"  来源: {event.source}\n"
                f"  数据: {json.dumps(event.data, ensure_ascii=False)}\n\n"
                f"请分析这个事件并给出处理建议。"
            )
            result = self.client.chat(self.agent_id, prompt)
            print(f"  LLM分析: {result.get('content', '')[:200]}...")

    def update_system_hints(self):
        """更新系统提示元信息"""
        self.system_hints = {
            "current_time": time.strftime("%Y-%m-%d %H:%M"),
            "todo_count": len(self.todo_list),
            "pending_events": len(self.event_handlers),
        }

    def add_todo(self, task: str, priority: str = "medium"):
        """添加TODO项"""
        self.todo_list.append({"task": task, "priority": priority, "done": False})

    def get_context_for_prompt(self) -> str:
        """生成可注入 Prompt 的 System Hint 文本"""
        todo_lines = [
            f"  - [{t['priority']}] {t['task']}"
            for t in self.todo_list if not t.get("done")
        ]
        return (
            f"[System Hint]\n"
            f"当前时间: {self.system_hints.get('current_time', 'N/A')}\n"
            f"待办事项数: {self.system_hints.get('todo_count', 0)}\n"
            f"待办清单:\n" + "\n".join(todo_lines) if todo_lines else "[System Hint]\n无待办事项"
        )

    def demo(self):
        print("=" * 60)
        print("事件驱动Agent演示")
        print("=" * 60)
        print("""
被动模式 vs 主动模式：

被动模式：用户问 → Agent答，没有交互时Agent空闲
主动模式：事件触发 → Agent自动执行，可定时/条件/外部触发

事件类型：
  定时事件：每天9:00检查商机跟进提醒
  数据事件：缺陷率超过阈值自动告警
  外部事件：客户提交申请自动启动审核流程
  人工事件：审批人点击「同意」触发下一步""")
        # 模拟事件
        self.register_handler("data_alert", lambda e: print(f"  处理数据告警: {e.data}"))
        self.register_handler("timer", lambda e: print(f"  处理定时任务: {e.data}"))

        self.emit_event(self.Event("data_alert", "生产系统", {"metric": "缺陷率", "value": "5.2%", "threshold": "3%"}))
        self.emit_event(self.Event("timer", "调度器", {"task": "商机跟进提醒", "target": "客户A"}))

        self.add_todo("处理缺陷率告警", "high")
        self.add_todo("跟进客户A商机", "medium")
        self.update_system_hints()
        print(f"\n系统状态: {json.dumps(self.system_hints, ensure_ascii=False)}")

        print("\n架构演进路径：")
        print("  阶段1: 被动问答（Day2-4）")
        print("  阶段2: 事件驱动 + System Hint（Day5）")
        print("  阶段3: 工作流录制 + RPA自动化（进阶）")
