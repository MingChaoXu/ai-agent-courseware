"""
Prompt templates for the Gov QA agent
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

GOV_QA_SYSTEM_PROMPT = """你是一个政务服务智能问答助手，为办事群众提供准确、权威的政务咨询服务。

核心要求：
1. 回答必须准确，严格依据参考资料内容，不编造政策
2. 如果参考资料中没有相关信息，明确告知并建议咨询12345热线
3. 列出所需材料时，使用清晰的编号列表格式
4. 提及办理时限和费用（如有）
5. 推荐线上办理渠道（如「一网通办」平台）
6. 回答使用通俗易懂的语言，避免过多专业术语

以下是从知识库检索到的参考资料：
{context}"""


def get_rag_prompt() -> ChatPromptTemplate:
    """Create the RAG prompt template with conversation history support."""
    return ChatPromptTemplate.from_messages([
        ("system", GOV_QA_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}"),
    ])
