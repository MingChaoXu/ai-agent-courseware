"""
课题2: 制造领域工业知识库（LCEL + 检索参数调优）
==================================================
- 步骤1: 用 LCEL 构建工业运维 RAG
- 步骤2: 工业知识问答测试
- 步骤3: 检索参数调优实验（不同 top_k 的影响）
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from shared_utils import get_llm, get_embeddings, format_docs, check_api_config, DATA_DIR


# ============================================================
#  课题2: 制造领域工业知识库（LCEL + 检索参数调优）
# ============================================================

def exercise2_step1_build_rag():
    """步骤1: 一步构建工业运维 RAG（复用课题1的 LCEL 模式）"""
    print("=" * 60)
    print("课题2: 制造领域工业知识库")
    print("步骤1: 用 LCEL 构建工业运维 RAG")
    print("=" * 60)
    print("""
本课题复用课题1的 LCEL RAG 模式，关键差异：
  - 术语精确性要求高（设备型号、故障代码不能模糊匹配）
  - chunk_size 设为 800（维修步骤不宜截断）
  - temperature 设为 0.2（工业场景需要确定性回答）
  - 回答需结构化：现象→原因→步骤→预防
    """)

    # 加载工业知识库
    docs_path = os.path.join(DATA_DIR, "industrial_kb.json")
    if not os.path.exists(docs_path):
        print(f"⚠️ 数据文件不存在: {docs_path}")
        print("  请先运行: python exercises/common/gen_sample_data.py")
        return None, None

    with open(docs_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    # 分块（工业场景 chunk_size 更大）
    print(f"\n--- 文本分块（chunk_size=800）---")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    texts = [f"标题：{doc['title']}\n{doc['content']}" for doc in docs]
    chunks = splitter.create_documents(texts)
    print(f"原始文档: {len(docs)} 条 → 分块后: {len(chunks)} 个文本块")
    for doc in docs:
        print(f"  已加载: {doc['title']}")

    # 构建 FAISS
    print(f"\n--- 构建 FAISS 索引 ---")
    try:
        embeddings = get_embeddings()
        vectorstore = FAISS.from_documents(chunks, embeddings)
        print(f"✅ FAISS 索引构建成功！共 {vectorstore.index.ntotal} 个向量")
    except Exception as e:
        print(f"⚠️ Embedding API 调用失败: {e}")
        return None, None

    # 构建 LCEL Chain
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个工业设备运维知识助手，帮助工厂维修工程师快速查找设备故障原因和维修方案。\n\n"
         "核心要求：\n"
         "1. 严格依据参考资料回答，不编造设备参数\n"
         "2. 回答格式：故障现象 → 可能原因 → 处理步骤 → 预防措施\n"
         "3. 涉及安全操作的，必须标注安全警告 ⚠️\n"
         "4. 如果问题不明确，追问设备型号和故障代码\n\n"
         "参考资料：\n{context}"),
        ("human", "{question}"),
    ])

    llm = get_llm(temperature=0.2, max_tokens=2000)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("\n✅ 工业 RAG Chain 构建完成！")
    print("  配置: chunk_size=800, temperature=0.2, top_k=3")
    return rag_chain, vectorstore


def exercise2_step2_test(rag_chain):
    """步骤2: 工业知识问答测试"""
    print("\n" + "=" * 60)
    print("步骤2: 工业知识问答测试")
    print("=" * 60)

    if rag_chain is None:
        print("⚠️ RAG Chain 未构建，跳过测试")
        return

    test_queries = [
        "CNC主轴有异响是什么原因？",
        "变频器报E001过流保护怎么处理？",
        "PLC和上位机通讯不上怎么排查？",
    ]

    for q in test_queries:
        print(f"\n👤 工程师: {q}")
        try:
            answer = rag_chain.invoke(q)
            print(f"🤖 知识库: {answer}")
        except Exception as e:
            print(f"⚠️ 调用失败: {e}")


def exercise2_step3_retrieval_comparison(vectorstore):
    """步骤3: 检索参数调优实验 — 不同 top_k 和 chunk_size 的影响"""
    print("\n" + "=" * 60)
    print("步骤3: 检索参数调优实验")
    print("=" * 60)

    if vectorstore is None:
        print("⚠️ 向量知识库未构建，跳过")
        return

    print("""
RAG 效果取决于检索质量，两个关键参数：
  - top_k: 检索返回的文档数量
    → 太少：可能漏掉关键信息
    → 太多：引入噪音，LLM 可能被无关内容干扰
  - chunk_size: 文本分块大小
    → 太小：上下文被切断，语义不完整
    → 太大：一个块包含多个话题，检索精度下降
    """)

    query = "变频器报E001过流保护怎么处理？"
    llm = get_llm(temperature=0.2)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是工业运维助手，请基于参考资料回答。\n\n参考资料：\n{context}"),
        ("human", "{question}"),
    ])

    for k in [1, 3, 5]:
        print(f"\n--- top_k={k} ---")
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(query)
        print(f"  检索到 {len(docs)} 个文档块:")
        for i, doc in enumerate(docs):
            print(f"    块{i+1}: {doc.page_content[:60]}...")

        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt_template
            | llm
            | StrOutputParser()
        )
        try:
            answer = chain.invoke(query)
            print(f"  回答: {answer[:150]}...")
        except Exception as e:
            print(f"  ⚠️ 调用失败: {e}")

    print("""
💡 调优建议：
  - 精确术语查询（故障代码）：top_k=1-2 即可
  - 模糊诊断查询（异响原因）：top_k=3-5 更好
  - 生产环境推荐：先用较大 top_k 检索，再用 Reranker 重排序
    """)


def run_exercise2():
    """运行课题2完整流程"""
    rag_chain, vectorstore = exercise2_step1_build_rag()
    exercise2_step2_test(rag_chain)
    exercise2_step3_retrieval_comparison(vectorstore)
    print("\n✅ 课题2完成！你已掌握 LCEL RAG 构建和检索参数调优。")


if __name__ == "__main__":
    check_api_config()
    run_exercise2()
