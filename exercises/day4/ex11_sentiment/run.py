"""
课题11: 金融领域舆情洞察
========================
基于 PydanticOutputParser 构建舆情分析报告结构化输出，
使用 LCEL Chain 实现情感分析、风险研判和建议生成。

技术栈：LangChain 1.x（PydanticOutputParser, ChatPromptTemplate, LCEL）
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field


# ============================================================
#  课题11: 金融领域舆情洞察
# ============================================================

class SentimentResult(BaseModel):
    """舆情情感分析结果"""
    item: str = Field(description="舆情条目摘要")
    sentiment: str = Field(description="情感判断：正面/中性/负面")
    sentiment_score: float = Field(description="情感得分(-1到+1)")
    risk_level: str = Field(description="舆情分级：红色预警/黄色关注/绿色正常")
    key_topic: str = Field(description="核心主题")
    suggested_action: str = Field(description="建议措施")


class SentimentReport(BaseModel):
    """舆情分析报告"""
    overall_sentiment: str = Field(description="整体舆情倾向")
    red_count: int = Field(description="红色预警数")
    yellow_count: int = Field(description="黄色关注数")
    green_count: int = Field(description="绿色正常数")
    hot_topics: list[str] = Field(description="热点关键词列表")
    items: list[SentimentResult] = Field(description="逐条分析")
    summary: str = Field(description="综述与建议")


def exercise11_run():
    print("=" * 60)
    print("课题11: 金融领域舆情洞察")
    print("=" * 60)

    llm = get_llm(temperature=0.1)

    print("\n--- 步骤1: 构建舆情分析 LCEL Chain（PydanticOutputParser） ---")

    parser = PydanticOutputParser(pydantic_object=SentimentReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个舆情洞察助手，帮助银行监测和分析品牌舆情。\n\n"
         "分析能力：\n"
         "1. 【情感分析】判断舆情正面/中性/负面，给出情感得分(-1到+1)\n"
         "2. 【热点提取】识别高频关键词和主题\n"
         "3. 【风险研判】判断舆情是否可能升级为公关危机\n"
         "4. 【报告生成】生成舆情分析报告\n\n"
         "舆情分级：\n"
         "- 红色预警：负面情感>0.7，涉及监管/诉讼/群体事件\n"
         "- 黄色关注：负面情感0.3-0.7，有传播趋势\n"
         "- 绿色正常：正面/中性为主，无风险迹象\n\n"
         "{format_instructions}"),
        ("human", "请分析以下舆情数据，给出情感的逐条判断、风险研判和建议：\n\n{news_data}"),
    ])

    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    sentiment_chain = prompt | llm | parser
    print("舆情分析 Chain 构建完成")

    # 步骤2: 舆情分析
    print("\n--- 步骤2: 舆情分析测试 ---")
    news_items = """
舆情数据（2026年6月25日-7月1日）：

1. [微博] 「XX银行APP又崩了，转账转了半小时！」#XX银行APP故障# 阅读量12万，评论856条
2. [知乎] 「在XX银行办房贷是什么体验」 - 作者分享了3天批贷的顺利经历，获赞320
3. [抖音] 博主曝光XX银行信用卡隐藏收费项目，视频播放量45万，转发2000+
4. [小红书] 「XX银行新出的数字藏品太酷了」 - 正面种草帖，互动800+
5. [贴吧] 多人反映XX银行网点排队2小时以上，帖子被反复引用
6. [新闻] XX银行发布半年报，净利润同比增长12%，多家券商给出买入评级"""

    try:
        report: SentimentReport = sentiment_chain.invoke({"news_data": news_items})
        print(f"  整体舆情: {report.overall_sentiment}")
        print(f"  红/黄/绿: {report.red_count}/{report.yellow_count}/{report.green_count}")
        print(f"  热点: {', '.join(report.hot_topics[:5])}")
        for item in report.items[:4]:
            icon = "🔴" if item.risk_level == "红色预警" else ("🟡" if item.risk_level == "黄色关注" else "🟢")
            print(f"  {icon} [{item.sentiment}] {item.item[:40]}... → {item.suggested_action[:40]}")
        print(f"  综述: {report.summary[:200]}...")
    except Exception as e:
        print(f"  [结构化输出失败: {e}]，降级为文本模式...")
        try:
            text_chain = prompt | llm | StrOutputParser()
            result = text_chain.invoke({"news_data": news_items})
            print(f"  {result[:400]}...")
        except Exception as e2:
            print(f"  [文本模式也失败: {e2}]")

    print("\n课题11完成！")


if __name__ == "__main__":
    exercise11_run()
