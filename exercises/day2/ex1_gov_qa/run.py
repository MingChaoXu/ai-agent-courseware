"""
课题1: 政务服务智能问答助手（LCEL RAG Chain + FAISS）
======================================================
- 步骤1: 初始化 ChatOpenAI
- 步骤2: 用 ChatPromptTemplate 定义 RAG 提示模板
- 步骤3: 构建 FAISS 向量知识库
- 步骤4: 用 LCEL 组装 RAG Chain
- 步骤5: 多轮问答测试
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage

from shared_utils import get_llm, get_embeddings, format_docs, check_api_config, DATA_DIR


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


if __name__ == "__main__":
    check_api_config()
    run_exercise1()
