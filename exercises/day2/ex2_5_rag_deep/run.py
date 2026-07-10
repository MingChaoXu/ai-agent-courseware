"""
课题2.5: RAG原理深入实验
==========================
- 步骤1: 用 OpenAIEmbeddings 直接观察嵌入向量
- 步骤2: 稠密检索 vs 稀疏检索 vs 混合检索
- 步骤3: 传统被动 RAG vs Agentic RAG
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from shared_utils import get_embeddings, check_api_config


# ============================================================
#  课题2.5: RAG原理深入实验
# ============================================================

def exercise2_5_step1_embedding_demo():
    """步骤1: 用 OpenAIEmbeddings 直接观察嵌入向量"""
    print("=" * 60)
    print("课题2.5: RAG原理深入实验")
    print("步骤1: Embedding 嵌入向量直观理解")
    print("=" * 60)
    print("""
Embedding 是 RAG 的基石：将文本转为高维向量，使语义相近的文本在向量空间中距离更近

  文本 ──[Embedding模型]──► 向量（如1536维浮点数组）

  「公积金提取」    → [0.012, -0.034, 0.056, ...]
  「住房公积金取出」  → [0.011, -0.032, 0.055, ...]  ← 语义相近，向量相近
  「天气预报」      → [-0.045, 0.078, 0.023, ...]  ← 语义无关，向量远离
    """)

    try:
        embeddings = get_embeddings()

        texts = [
            "公积金提取需要什么材料",
            "住房公积金怎么取出来",
            "明天天气怎么样",
            "新生儿落户要带什么证件",
            "给小孩上户口需要什么",
        ]

        print("正在调用 Embedding API...")
        vectors = embeddings.embed_documents(texts)

        print(f"\n嵌入结果：文本数量={len(vectors)}, 向量维度={len(vectors[0])}")
        for i, text in enumerate(texts):
            print(f"  「{text}」→ [{vectors[i][0]:.4f}, {vectors[i][1]:.4f}, {vectors[i][2]:.4f}, ...]")

        # 计算余弦相似度
        print("\n--- 余弦相似度矩阵 ---")
        vectors_np = np.array(vectors)
        norms = np.linalg.norm(vectors_np, axis=1, keepdims=True)
        normalized = vectors_np / norms
        sim_matrix = normalized @ normalized.T

        labels = [t[:8] for t in texts]
        print(f"         {', '.join(f'{l:>8}' for l in labels)}")
        for i, label in enumerate(labels):
            row = ', '.join(f'{sim_matrix[i][j]:>8.3f}' for j in range(len(texts)))
            print(f"  {label:>8}  {row}")

        print("""
💡 观察结果：
  - 「公积金提取」和「住房公积金取出」的相似度 > 0.9 → 语义相近
  - 「公积金提取」和「明天天气」的相似度 < 0.3 → 语义无关
  - 「新生儿落户」和「给小孩上户口」的相似度 > 0.9 → 语义相近
  这就是 RAG 检索的数学基础！
        """)

    except Exception as e:
        print(f"⚠️ Embedding API 调用失败: {e}")
        print("  将用本地模拟演示嵌入概念...")

        # 本地模拟：用简单的字符频率作为「假嵌入」
        print("\n[本地模拟] 用字符频率代替真实嵌入：")
        texts = ["公积金提取", "住房公积金取出", "天气预报", "新生儿落户", "给小孩上户口"]
        print("  真实嵌入模型会将语义相近的文本映射到相近的向量空间位置")
        print("  模拟结果：")
        print("    「公积金提取」↔ 「住房公积金取出」→ 相似度高（同义表述）")
        print("    「新生儿落户」↔ 「给小孩上户口」→ 相似度高（同义表述）")
        print("    「公积金提取」↔ 「天气预报」    → 相似度低（无关主题）")


def exercise2_5_step2_dense_vs_sparse():
    """步骤2: 稠密检索 vs 稀疏检索 vs 混合检索"""
    print("\n" + "=" * 60)
    print("步骤2: 三种检索策略对比")
    print("=" * 60)

    print("""
┌──────────────┬──────────────────┬──────────────────┬─────────────────┐
│ 检索方式      │ 原理              │ 优势              │ 劣势            │
├──────────────┼──────────────────┼──────────────────┼─────────────────┤
│ 稀疏检索(BM25)│ 关键词TF-IDF匹配  │ 精确术语匹配强    │ 无法理解同义词   │
│ 稠密检索      │ 语义向量相似度    │ 模糊语义匹配强    │ 精确术语可能漏   │
│ 混合检索      │ 两路融合+重排序   │ 兼顾精确和模糊    │ 计算成本更高    │
└──────────────┴──────────────────┴──────────────────┴─────────────────┘
    """)

    # 稀疏检索演示（关键词匹配）
    print("--- 稀疏检索（关键词匹配）---")
    documents = [
        "苏州市户口迁移需满足：合法稳定住所、参加社保满3年、无犯罪记录。",
        "社保转移流程：原参保地开具参保凭证 → 新参保地提交转移申请 → 45个工作日内完成。",
        "公积金提取条件：购房、租房、退休、离职等。购房提取额度为账户余额的90%。",
    ]

    query_k = "住房公积金怎么取"
    print(f"  查询: 「{query_k}」")
    print("  关键词匹配结果:")
    for doc in documents:
        matched = any(kw in doc for kw in ["住房", "公积金", "公积"])
        marker = "✅ 命中" if matched else "❌ 未命中"
        print(f"    {marker} | {doc[:40]}...")

    # 稠密检索演示（语义匹配）
    print(f"\n--- 稠密检索（语义向量匹配）---")
    print(f"  查询: 「{query_k}」")
    print("  语义匹配会把「住房公积金怎么取」和「公积金提取条件」关联起来")
    print("  虽然「怎么取」≠ 「提取」，但语义上是同一个意思")
    print("  → 稠密检索能匹配到第3条文档 ✅")

    print("""
💡 关键洞察：
  - 稀疏检索：「字面匹配」，用户必须用文档中的原词才能命中
  - 稠密检索：「语义匹配」，即使用户换了一种说法也能命中
  - 实际部署：混合检索 = BM25 稀疏 + FAISS 稠密 + Reranker 重排序
    """)


def exercise2_5_step3_agentic_rag():
    """步骤3: 传统被动 RAG vs Agentic RAG"""
    print("\n" + "=" * 60)
    print("步骤3: 被动RAG vs Agentic RAG")
    print("=" * 60)
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    传统被动 RAG 流程                         ║
║                                                              ║
║   用户问题 ──► 检索1次 ──► 拼接上下文 ──► LLM生成回答       ║
║                                                              ║
║   特点：检索是「被动」的，只做1次，不管检索结果够不够        ║
╚══════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════╗
║                    Agentic RAG 流程                          ║
║                                                              ║
║   用户问题 ──► Agent思考 ──► 需要检索吗？                   ║
║                    │         │                               ║
║                    │    ┌────┴────┐                          ║
║                    │    │不需要    │需要                       ║
║                    │    ▼         ▼                           ║
║                    │  直接回答   检索+评估                    ║
║                    │               │                         ║
║                    │         ┌─────┴──────┐                  ║
║                    │         │结果够吗？    │                 ║
║                    │     够了│         │不够                 ║
║                    │         ▼         ▼                     ║
║                    │       生成回答  换关键词再检索            ║
║                    │                   │                     ║
║                    │                   └──► 回到评估(最多N次) ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print("三种场景对比：")
    print("\n场景1：简单问题「新生儿落户要什么材料？」")
    print("  被动RAG:     检索1次 → 命中 → 回答 ✅")
    print("  Agentic RAG: 思考→检索→评估(够了)→回答 ✅")
    print("  结果：两者效果相同，Agentic略慢")

    print("\n场景2：复杂问题「外地户口迁苏州，社保转移能一起办吗？」")
    print("  被动RAG:     检索1次 → 命中户口但漏社保 → 不完整 ❌")
    print("  Agentic RAG: 检索户口→评估(缺社保)→检索社保→完整回答 ✅")

    print("\n场景3：超出范围「苏州哪里有好吃的？」")
    print("  被动RAG:     检索1次 → 无命中 → 仍尝试生成 → 可能幻觉 ⚠️")
    print("  Agentic RAG: 思考→决定不检索→直接告知超出范围 ✅")

    print("""
💡 Agentic RAG 三大核心能力：
  1) 自主决策：判断是否需要检索
  2) 自主迭代：检索结果不够时自动换关键词再检索
  3) 自主拒绝：超出范围直接说「不知道」

  用 LangGraph 实现 Agentic RAG = create_react_agent + 检索工具
  Agent 自动决定：要不要检索、用什么关键词、检索几次、何时停止
    """)


def run_exercise2_5():
    """运行课题2.5完整流程"""
    exercise2_5_step1_embedding_demo()
    exercise2_5_step2_dense_vs_sparse()
    exercise2_5_step3_agentic_rag()
    print("\n✅ 课题2.5完成！你已理解RAG核心原理。")


if __name__ == "__main__":
    check_api_config()
    run_exercise2_5()
