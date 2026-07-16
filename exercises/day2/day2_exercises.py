"""
Day 2 实战课题：LangChain实战入门 + 知识库与RAG原理
===================================================
课题1:   政务服务智能问答助手（LCEL RAG Chain + FAISS）
课题2:   制造领域工业知识库（LCEL + 检索参数调优）
课题2.5: RAG原理深入实验（原生 Embedding + 检索对比）
课题3:   医疗领域病历生成（PydanticOutputParser 结构化输出）
课题3.5: 上下文压缩策略实验（LangChain Memory 对比）

技术栈：LangChain 原生 API（ChatOpenAI, FAISS, LCEL, OutputParser）+ LangGraph（create_react_agent）
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys
import os
import json
import numpy as np

# ============================================================
#  环境配置 & LangChain 核心导入
# ============================================================

# 加载 .env 配置
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(_env_path)

# ---- LangChain 核心 ----
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ============================================================
#  公共辅助函数
# ============================================================

def get_llm(temperature: float = 0.3, max_tokens: int = 2000) -> ChatOpenAI:
    """创建 LLM 实例 — 所有课题共用"""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("OPENAI_API_BASE", ""),
        temperature=temperature,
        max_tokens=max_tokens,
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


def check_api_config():
    """检查 API 配置"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_API_BASE", "")
    if not api_key or api_key == "sk-your-api-key-here":
        print("[警告] 未配置 OPENAI_API_KEY，请在 .env 文件中设置")
        print(f"  .env 文件位置: {_env_path}")
        return False
    if not base_url:
        print("[警告] 未配置 OPENAI_API_BASE，请在 .env 文件中设置")
        return False
    print(f"  API 地址: {base_url}")
    print(f"  模型名称: {os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')}")
    print(f"  嵌入模型: {os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-3-small')}")
    print(f"  API Key:  {'已配置 ✓' if api_key else '未配置 ✗'}")
    return True


# ============================================================
#  课题1: 政务服务智能问答助手（LCEL RAG Chain）
# ============================================================

def exercise1_step1_init_llm():
    """步骤1: 初始化 ChatOpenAI — 理解 LLM 是一切的基础"""
    print("=" * 60)
    print("课题1: 政务服务智能问答助手")
    print("步骤1: 初始化 ChatOpenAI")
    print("=" * 60)
    print("""
本课题用 LangChain LCEL 构建 RAG 问答系统，四步流程：
  ① ChatOpenAI 初始化
  ② ChatPromptTemplate 定义提示模板
  ③ FAISS + OpenAIEmbeddings 构建向量检索
  ④ LCEL 管道（retriever | prompt | llm | parser）

LCEL = LangChain Expression Language
  用管道操作符 | 串联组件：retriever | prompt | llm | parser
  等价于函数组合：parser(llm(prompt(retriever(question))))
    """)

    llm = get_llm()
    print("ChatOpenAI 初始化参数：")
    print(f"  model     = {os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')}")
    print(f"  base_url  = {os.getenv('OPENAI_API_BASE', '')}")
    print(f"  temperature = 0.3")
    print(f"  max_tokens  = 2000")

    # 快速测试
    print("\n快速测试 LLM 连接...")
    try:
        response = llm.invoke([HumanMessage(content="请用一句话介绍你自己。")])
        print(f"✅ LLM 响应正常: {response.content[:80]}...")
    except Exception as e:
        print(f"⚠️ LLM 调用失败: {e}")
        print("  请检查 .env 中的 API 配置")

    return llm


def exercise1_step2_create_prompt():
    """步骤2: 用 ChatPromptTemplate 定义 RAG 提示模板"""
    print("\n" + "=" * 60)
    print("步骤2: ChatPromptTemplate 构建 RAG 提示模板")
    print("=" * 60)
    print("""
ChatPromptTemplate = 系统 Prompt + 变量占位符
  - SystemMessage: 定义 Agent 角色和行为规则
  - {context} 占位符: 注入检索到的知识库内容
  - {question} 占位符: 注入用户问题
  - "消息" 和 "变量" 分离，模板可复用
    """)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个政务服务智能问答助手，为办事群众提供政务咨询服务。\n\n"
         "核心要求：\n"
         "1. 回答必须准确，严格依据参考资料内容，不编造政策\n"
         "2. 如果参考资料中没有相关信息，明确告知并建议咨询12345热线\n"
         "3. 列出所需材料时，使用清晰的编号列表格式\n"
         "4. 提及办理时限和费用（如有）\n"
         "5. 推荐线上办理渠道（如「一网通办」平台）\n\n"
         "以下是从知识库检索到的参考资料：\n{context}"),
        ("human", "{question}"),
    ])

    print("提示模板结构：")
    for msg_type, content in prompt.messages:
        role = "System" if msg_type == "system" else "Human"
        print(f"  [{role}] {content[:60]}...")

    return prompt


def exercise1_step3_build_vectorstore():
    """步骤3: 构建 FAISS 向量知识库 — 理解向量化流程"""
    print("\n" + "=" * 60)
    print("步骤3: 构建 FAISS 向量知识库")
    print("=" * 60)
    print("""
FAISS 向量知识库构建流程：
  原始文本 → RecursiveCharacterTextSplitter(分块) → OpenAIEmbeddings(嵌入) → FAISS(索引)

关键参数：
  - chunk_size: 分块大小，政务 FAQ 建议较小(500)，避免多话题混在一个块
  - chunk_overlap: 重叠字符数，保证上下文不截断
  - embeddings: 嵌入模型，将文本转为高维向量
    """)

    # 加载 FAQ 数据
    faq_path = os.path.join(DATA_DIR, "gov_faq.json")
    if not os.path.exists(faq_path):
        print(f"⚠️ 数据文件不存在: {faq_path}")
        print("  请先运行: python exercises/common/gen_sample_data.py")
        return None

    with open(faq_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    # 拼接文档
    documents = []
    for faq in faqs:
        text = f"问题：{faq['question']}\n类别：{faq['category']}\n答案：{faq['answer']}"
        documents.append(text)
        print(f"  已加载: [{faq['category']}] {faq['question']}")

    # 分块
    print(f"\n--- 文本分块 ---")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.create_documents(documents)
    print(f"原始文档: {len(documents)} 条")
    print(f"分块后:   {len(chunks)} 个文本块")
    print(f"参数: chunk_size=500, chunk_overlap=50")

    # 向量化 & 构建 FAISS 索引
    print(f"\n--- 向量化 & 构建 FAISS 索引 ---")
    print("  调用 Embedding API 将每个文本块转为向量...")
    try:
        embeddings = get_embeddings()
        vectorstore = FAISS.from_documents(chunks, embeddings)
        print(f"✅ FAISS 索引构建成功！共 {vectorstore.index.ntotal} 个向量")

        # 测试检索
        print("\n--- 快速检索测试 ---")
        test_query = "新生儿落户"
        results = vectorstore.similarity_search(test_query, k=2)
        print(f"查询: 「{test_query}」")
        for i, doc in enumerate(results):
            print(f"  结果{i+1}: {doc.page_content[:80]}...")

        return vectorstore
    except Exception as e:
        print(f"⚠️ Embedding API 调用失败: {e}")
        print("  RAG 知识库需要 Embedding API，请检查 .env 中的 EMBEDDING_MODEL_NAME 配置")
        return None


def exercise1_step4_create_rag_chain(llm, prompt, vectorstore):
    """步骤4: 用 LCEL 组装 RAG Chain — 理解管道式组合"""
    print("\n" + "=" * 60)
    print("步骤4: LCEL 组装 RAG Chain")
    print("=" * 60)

    if vectorstore is None:
        print("⚠️ 向量知识库未构建，跳过此步骤")
        return None

    # 创建检索器
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},  # 检索 Top-3 最相关文档
    )
    print(f"检索器配置: search_type=similarity, k=3（检索最相关的3个文本块）")

    # ---- LCEL 管道组装 ----
    print("\nLCEL 管道组装：")
    print("  rag_chain = (")
    print("      {'context': retriever | format_docs, 'question': RunnablePassthrough()}")
    print("      | prompt")
    print("      | llm")
    print("      | StrOutputParser()")
    print("  )")
    print()
    print("数据流：")
    print("  用户问题 ──► RunnablePassthrough 传递问题")
    print("                │")
    print("                ├──► retriever 检索相关文档 → format_docs 格式化为文本 → {context}")
    print("                │")
    print("                └──► 原始问题 → {question}")
    print("                │")
    print("                ▼")
    print("            prompt(注入 context + question)")
    print("                │")
    print("                ▼")
    print("            llm(生成回答)")
    print("                │")
    print("                ▼")
    print("            StrOutputParser(提取文本)")

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("\n✅ RAG Chain 组装完成！")
    return rag_chain


def exercise1_step5_test(rag_chain):
    """步骤5: 多轮问答测试"""
    print("\n" + "=" * 60)
    print("步骤5: 多轮问答测试")
    print("=" * 60)

    if rag_chain is None:
        print("⚠️ RAG Chain 未构建，跳过测试")
        return

    test_questions = [
        "新生儿落户需要什么材料？",
        "社保怎么从外地转过来？",
        "公积金最多能贷多少？",
        "我想办理离婚手续怎么办？",
    ]

    for q in test_questions:
        print(f"\n👤 用户: {q}")
        try:
            answer = rag_chain.invoke(q)
            print(f"🤖 助手: {answer}")
        except Exception as e:
            print(f"⚠️ 调用失败: {e}")

    print("""
💡 对比思考：
  - 前3个问题在知识库中有对应内容 → 回答准确
  - 第4个问题可能不在知识库范围内 → 依 system prompt 应建议咨询12345
  - RAG 的核心价值：让 LLM 基于「事实」而非「记忆」回答，减少幻觉
    """)


def run_exercise1():
    """运行课题1完整流程"""
    llm = exercise1_step1_init_llm()
    prompt = exercise1_step2_create_prompt()
    vectorstore = exercise1_step3_build_vectorstore()
    rag_chain = exercise1_step4_create_rag_chain(llm, prompt, vectorstore)
    exercise1_step5_test(rag_chain)
    print("\n✅ 课题1完成！你已掌握 LCEL RAG Chain 的构建方法。")


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


# ============================================================
#  课题3: 医疗领域病历生成（PydanticOutputParser 结构化输出）
# ============================================================

class MedicalRecord(BaseModel):
    """门诊病历结构化输出模型 — Pydantic 定义输出格式"""
    chief_complaint: str = Field(description="主诉：患者主要症状及持续时间")
    present_illness: str = Field(description="现病史：症状发生发展过程")
    past_history: str = Field(description="既往史：既往疾病、手术、过敏史")
    physical_examination: str = Field(description="体格检查：生命体征和阳性体征")
    preliminary_diagnosis: str = Field(description="初步诊断：根据病史和体征得出的诊断")
    treatment_plan: str = Field(description="处理意见：用药处方、检查建议、注意事项")


def exercise3_step1_pydantic_parser():
    """步骤1: PydanticOutputParser — 让 LLM 输出结构化 JSON"""
    print("=" * 60)
    print("课题3: 医疗领域病历生成")
    print("步骤1: PydanticOutputParser 结构化输出")
    print("=" * 60)
    print("""
问题：LLM 默认输出自由文本，但业务需要结构化数据（JSON）

PydanticOutputParser 的作用：
  1) 定义 Pydantic 模型 → 自动生成 JSON Schema
  2) 将 Schema 注入 Prompt → LLM 按 Schema 格式输出
  3) 解析 LLM 输出 → 自动转为 Pydantic 对象（带类型校验）

流程：
  Pydantic 模型 → parser.get_format_instructions() → 注入 Prompt
  LLM 输出 JSON → parser.parse() → MedicalRecord 对象
    """)

    parser = PydanticOutputParser(pydantic_object=MedicalRecord)

    print("MedicalRecord 字段：")
    for name, field in MedicalRecord.model_fields.items():
        print(f"  - {name}: {field.description}")

    print(f"\n自动生成的格式指令（将注入 Prompt）：")
    format_instr = parser.get_format_instructions()
    print(f"  {format_instr[:200]}...")

    return parser


def exercise3_step2_build_chain(parser):
    """步骤2: 构建 LLMChain — ChatPromptTemplate + PydanticOutputParser"""
    print("\n" + "=" * 60)
    print("步骤2: 构建 LCEL Chain（Prompt + LLM + Parser）")
    print("=" * 60)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个门诊病历辅助生成助手，帮助基层医生快速生成规范的门诊病历。\n\n"
         "生成规则：\n"
         "1. 严格按照门诊病历规范格式生成\n"
         "2. 使用规范医学术语，不使用口语化表达\n"
         "3. 药品使用通用名，标注剂量、用法、频次\n"
         "4. 需要进一步检查的，明确标注检查项目\n\n"
         "重要：本助手仅辅助生成病历草稿，最终诊断和处方必须由执业医师确认签字。\n\n"
         "{format_instructions}"),
        ("human", "请根据以下信息生成门诊病历：\n{input_text}"),
    ])

    # 将 format_instructions 部分绑定到 prompt
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    llm = get_llm(temperature=0.3)

    # LCEL Chain: prompt → llm → parser
    chain = prompt | llm | parser

    print("Chain 组装：")
    print("  prompt(注入 format_instructions) → llm → PydanticOutputParser")
    print("  prompt.partial(format_instructions=...) 预绑定格式指令")
    print("\n✅ 病历生成 Chain 构建完成！")
    return chain


def exercise3_step3_test(chain):
    """步骤3: 病历生成测试"""
    print("\n" + "=" * 60)
    print("步骤3: 病历生成测试")
    print("=" * 60)

    if chain is None:
        print("⚠️ Chain 未构建，跳过测试")
        return

    test_cases = [
        "患者女，45岁，反复头痛3天，伴恶心，无呕吐，既往高血压病史5年，目前服用氨氯地平5mg qd。查体：BP 155/95mmHg，神清，颈软。",
        "患儿男，3岁，发热2天，T 38.5℃，伴咳嗽、流涕，精神可，进食略减。查体：咽红，双肺呼吸音粗，未闻及啰音。",
    ]

    for case in test_cases:
        print(f"\n👤 医生输入: {case}")
        try:
            result = chain.invoke({"input_text": case})
            print(f"🤖 结构化病历:")
            print(f"  主诉:     {result.chief_complaint}")
            print(f"  现病史:   {result.present_illness}")
            print(f"  既往史:   {result.past_history}")
            print(f"  体格检查: {result.physical_examination}")
            print(f"  初步诊断: {result.preliminary_diagnosis}")
            print(f"  处理意见: {result.treatment_plan}")
            print(f"  ✅ 输出类型: {type(result).__name__}（Pydantic 模型，可序列化为 JSON/dict）")
        except Exception as e:
            print(f"⚠️ 生成失败: {e}")
            print("  Parser 解析失败时，LLM 输出格式可能不匹配，需调整 prompt 或重试")

    print("""
💡 PydanticOutputParser vs 纯文本输出：
  - 纯文本：LLM 自由输出，格式不可控，后续处理需正则解析
  - Parser：LLM 按 Schema 输出 JSON → 自动校验 + 类型转换 → 直接 .属性 访问
  - 注意：Parser 依赖 LLM 严格遵循格式，偶尔解析失败需重试
    """)


def run_exercise3():
    """运行课题3完整流程"""
    parser = exercise3_step1_pydantic_parser()
    chain = exercise3_step2_build_chain(parser)
    exercise3_step3_test(chain)
    print("\n✅ 课题3完成！你已掌握 PydanticOutputParser 结构化输出。")


# ============================================================
#  课题3.5: 上下文压缩策略实验（LangChain Memory 对比）
# ============================================================

def exercise3_5_step1_memory_basics():
    """步骤1: LangChain Memory 基础 — Buffer vs Summary"""
    print("=" * 60)
    print("课题3.5: 上下文压缩策略实验")
    print("步骤1: ConversationBufferMemory vs ConversationSummaryMemory")
    print("=" * 60)
    print("""
为什么需要 Memory 管理？
  - LLM 上下文窗口有限（4K/8K/128K tokens）
  - 长对话中，历史消息逐渐占满窗口
  - Token 越多 → 延迟越高、成本越大
  - 不同 Memory 策略 = 不同的「压缩」方式

LangChain 两种核心 Memory：
  ① ConversationBufferMemory  — 保留完整历史（不压缩）
  ② ConversationSummaryMemory — LLM 自动摘要历史（压缩）
    """)

    from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryMemory

    llm = get_llm()

    # ---- Buffer Memory（完整记忆）----
    print("--- ConversationBufferMemory（不压缩，全部保留）---")
    buffer_memory = ConversationBufferMemory(return_messages=True)

    # 模拟对话
    conversation = [
        ("user", "我想咨询公积金提取的问题，我叫张明"),
        ("assistant", "张先生你好，公积金提取有多种情形，请问您是购房提取还是租房提取？"),
        ("user", "购房提取，我买了XX小区的房子，花了200万"),
        ("assistant", "购房提取需要提供购房合同、房产证、身份证等材料。"),
        ("user", "身份证号是320506199001011234，手机号13812345678"),
        ("assistant", "已记录您的身份信息。提取额度上限为账户余额，留10%保证金。"),
        ("user", "那社保转移怎么办理？需要多久？"),
        ("assistant", "社保转移可以通过国家社会保险公共服务平台线上办理，一般45个工作日完成。"),
        ("user", "好的，另外我还想问问新生儿落户的事"),
        ("assistant", "新生儿落户需要：出生医学证明、父母结婚证、户口簿、身份证。"),
    ]

    for role, content in conversation:
        if role == "user":
            buffer_memory.chat_memory.add_user_message(content)
        else:
            buffer_memory.chat_memory.add_ai_message(content)

    buffer_msgs = buffer_memory.load_memory_variables({})
    buffer_text = str(buffer_msgs.get("history", ""))
    buffer_chars = len(buffer_text)
    est_buffer_tokens = buffer_chars // 4

    print(f"  保留消息数: {len(buffer_memory.chat_memory.messages)}")
    print(f"  总字符数:   {buffer_chars}")
    print(f"  估计 Token: ~{est_buffer_tokens}")

    # ---- Summary Memory（摘要压缩）----
    print(f"\n--- ConversationSummaryMemory（LLM 自动摘要压缩）---")
    try:
        summary_memory = ConversationSummaryMemory(llm=llm, return_messages=True)

        # 逐条添加（Summary Memory 会自动在每轮生成摘要）
        for role, content in conversation:
            if role == "user":
                summary_memory.chat_memory.add_user_message(content)
            else:
                summary_memory.chat_memory.add_ai_message(content)

        # 手动触发摘要生成
        summary_memory.predict_new_summary(
            summary_memory.chat_memory.messages,
            summary_memory.moving_summary_buffer
        )

        summary_msgs = summary_memory.load_memory_variables({})
        summary_text = str(summary_msgs.get("history", ""))
        summary_chars = len(summary_text)
        est_summary_tokens = summary_chars // 4

        print(f"  摘要后字符数: {summary_chars}")
        print(f"  估计 Token:   ~{est_summary_tokens}")
        print(f"  压缩率:       {summary_chars / buffer_chars * 100:.0f}%")
        print(f"  摘要内容:     {summary_text[:200]}...")

    except Exception as e:
        print(f"  ⚠️ Summary Memory 生成失败: {e}")
        print("  模拟压缩结果: 压缩率约30-50%，保留关键信息（姓名、身份证、业务类别）")

    print(f"""
💡 对比：
  ┌─────────────────────┬──────────┬─────────────────────────┐
  │ 策略                 │ 压缩率   │ 特点                    │
  ├─────────────────────┼──────────┼─────────────────────────┤
  │ BufferMemory(不压缩) │ 100%     │ 信息完整，但Token消耗大  │
  │ SummaryMemory(摘要)  │ ~30-50%  │ 保留要点，细节可能丢失  │
  └─────────────────────┴──────────┴─────────────────────────┘
    """)


def exercise3_5_step2_sliding_window():
    """步骤2: 滑动窗口策略（手动实现最常用的压缩方法）"""
    print("\n" + "=" * 60)
    print("步骤2: 滑动窗口策略 — 只保留最近 K 轮对话")
    print("=" * 60)
    print("""
滑动窗口是最简单、最常用的上下文压缩方法：
  - 只保留最近 K 轮对话（K 通常为 3-5）
  - 超出窗口的历史直接丢弃
  - 零成本、零延迟、实现简单

在 LangChain 中的用法：
  直接在构建 messages 时，截取 history[-K*2:]（每轮2条消息）
    """)

    # 模拟对话历史
    history = [
        HumanMessage(content="我想咨询公积金提取的问题，我叫张明"),
        AIMessage(content="张先生你好，公积金提取有多种情形，请问您是购房提取还是租房提取？"),
        HumanMessage(content="购房提取，买了XX小区的房子"),
        AIMessage(content="购房提取需要提供购房合同、房产证、身份证等材料。"),
        HumanMessage(content="身份证号是320506199001011234"),
        AIMessage(content="已记录您的身份信息。提取额度上限为账户余额。"),
        HumanMessage(content="社保转移怎么办理？"),
        AIMessage(content="社保转移可线上办理，45个工作日完成。"),
        HumanMessage(content="新生儿落户需要什么？"),
        AIMessage(content="需要出生医学证明、结婚证、户口簿。"),
        HumanMessage(content="落户后医保怎么变更？"),
    ]

    for K in [2, 3, 5]:
        window = history[-(K * 2):]  # 每轮2条消息
        chars = sum(len(m.content) for m in window)
        total_chars = sum(len(m.content) for m in history)
        print(f"\n  K={K}（保留最近{K}轮）: {len(window)}条消息, {chars}字符, 压缩率{chars/total_chars*100:.0f}%")
        for m in window:
            role = "👤" if isinstance(m, HumanMessage) else "🤖"
            print(f"    {role} {m.content[:40]}...")

    print("""
💡 滑动窗口的优缺点：
  ✅ 实现简单，零成本，零延迟
  ✅ 最近对话最重要，窗口策略符合直觉
  ❌ 早期重要信息（如用户姓名、身份证）可能被丢弃
  ❌ 无法根据内容重要性动态调整

  → 实际应用中，常将「滑动窗口 + 系统提示中保留关键实体」结合使用
    """)


def exercise3_5_step3_practical_tips():
    """步骤3: 实战压缩策略选择指南"""
    print("\n" + "=" * 60)
    print("步骤3: 实战压缩策略选择指南")
    print("=" * 60)
    print("""
┌──────────────────────┬──────────┬────────────────────────────────┐
│ 策略                  │ 压缩率   │ 适用场景                        │
├──────────────────────┼──────────┼────────────────────────────────┤
│ 不压缩(Buffer)        │ 0%       │ 短对话(<10轮)，调试阶段         │
│ 滑动窗口(K=3)         │ ~60%     │ 通用场景，最简单有效            │
│ 摘要(Summary)         │ ~50%     │ 长对话，需保留要点              │
│ 摘要+引用             │ ~40%     │ 合规/法律场景，需可追溯         │
│ 分级保留              │ ~30%     │ 超长对话，分层级保留            │
└──────────────────────┴──────────┴────────────────────────────────┘

LangChain 实现方式：
  1) ConversationBufferMemory        → 不压缩
  2) 手动截取 history[-K*2:]          → 滑动窗口
  3) ConversationSummaryMemory       → LLM 摘要
  4) ConversationSummaryBufferMemory → 摘要+缓冲（近期不压缩，远期摘要）

生产环境推荐：
  - 默认：ConversationSummaryBufferMemory（兼顾近期完整+远期摘要）
  - 简单场景：滑动窗口（零成本，够用）
  - 合规场景：摘要+引用（所有关键信息可回溯）
    """)


def run_exercise3_5():
    """运行课题3.5完整流程"""
    exercise3_5_step1_memory_basics()
    exercise3_5_step2_sliding_window()
    exercise3_5_step3_practical_tips()
    print("\n✅ 课题3.5完成！你已掌握上下文压缩策略。")


# ============================================================
#  主入口
# ============================================================

EXERCISES = {
    "1": ("课题1:   政务服务智能问答助手（实战层）", run_exercise1),
    "2": ("课题2:   制造领域工业知识库（实战层）", run_exercise2),
    "2.5": ("课题2.5: RAG原理深入实验（原理层）", run_exercise2_5),
    "3": ("课题3:   医疗领域病历生成（实战层）", run_exercise3),
    "3.5": ("课题3.5: 上下文压缩策略实验（原理层）", run_exercise3_5),
}

if __name__ == "__main__":
    print("=" * 60)
    print("Day 2: LangChain实战入门 + 知识库与RAG原理")
    print("=" * 60)
    print()
    check_api_config()
    print()

    print("可选课题：")
    for key, (desc, _) in EXERCISES.items():
        print(f"  {key:>3} - {desc}")
    print("  all  - 运行全部课题")
    print("  原理 - 仅运行原理层课题(2.5, 3.5)")
    print("  实战 - 仅运行实战层课题(1, 2, 3)")

    choice = input("\n请输入选项: ").strip()

    if choice == "all":
        for key in ["1", "2", "2.5", "3", "3.5"]:
            EXERCISES[key][1]()
    elif choice == "原理":
        for key in ["2.5", "3.5"]:
            EXERCISES[key][1]()
    elif choice == "实战":
        for key in ["1", "2", "3"]:
            EXERCISES[key][1]()
    elif choice in EXERCISES:
        EXERCISES[choice][1]()
    else:
        print(f"无效选项: {choice}")
