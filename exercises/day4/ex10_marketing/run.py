"""
课题10: 消费领域精准营销
========================
基于 PydanticOutputParser 构建客户画像结构化输出，
使用 LCEL Chain 实现 RFM 分群 + 差异化营销策略推荐。

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
#  课题10: 消费领域精准营销
# ============================================================

class CustomerProfile(BaseModel):
    """客户画像结构化输出"""
    customer_id: str = Field(description="客户ID")
    rfm_segment: str = Field(description="RFM分群：高价值/成长/流失风险/低价值")
    consumption_preference: list[str] = Field(description="偏好品类列表")
    shopping_habit: str = Field(description="购物习惯描述")
    marketing_strategy: str = Field(description="推荐营销策略")
    expected_roi: str = Field(description="预估ROI")


def exercise10_run():
    print("=" * 60)
    print("课题10: 消费领域精准营销")
    print("=" * 60)

    llm = get_llm()

    print("\n--- 步骤1: 构建精准营销 LCEL Chain（PydanticOutputParser） ---")
    print("""
精准营销 Chain 设计：
  ① Pydantic 定义 CustomerProfile 输出结构（RFM分群+营销策略）
  ② ChatPromptTemplate 注入客户数据 + format_instructions
  ③ LCEL: prompt → llm → PydanticOutputParser
  ④ 输出为 CustomerProfile 对象，直接访问字段
    """)

    parser = PydanticOutputParser(pydantic_object=CustomerProfile)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个精准营销助手，帮助零售企业分析客户数据并制定营销策略。\n\n"
         "核心能力：\n"
         "1. 【客户画像】根据消费记录、行为数据生成客户画像标签\n"
         "2. 【客户分群】基于RFM模型（最近消费时间/频次/金额）进行客户分群\n"
         "3. 【营销推荐】针对不同客户群推荐差异化营销策略\n"
         "4. 【效果预测】预估营销活动ROI\n\n"
         "客户分群参考：\n"
         "- 高价值客户：R近、F高、M高 → VIP维护、专属权益\n"
         "- 成长客户：R近、F中、M中 → 提升频次、交叉推荐\n"
         "- 流失风险：R远、F低、M高 → 召回优惠、个性化推荐\n"
         "- 低价值客户：R远、F低、M低 → 促销引流、降低服务成本\n\n"
         "{format_instructions}"),
        ("human", "请对以下客户生成画像分析，并推荐精准营销策略：\n\n{customer_data}"),
    ])

    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    # 支持多客户的 LCEL Chain
    profile_chain = prompt | llm | parser

    print("精准营销 Chain 构建完成")

    # 步骤2: 客户画像与营销推荐
    print("\n--- 步骤2: 客户画像与营销策略测试 ---")
    customer_data = """
客户ID: C20260001
基本信息：张女士，32岁，居住于市中心商圈
消费记录（近6个月）：
- 总消费：8,560元
- 消费频次：23次
- 最近消费：3天前
- 偏好品类：美妆(35%)、服饰(28%)、食品(22%)、家居(15%)
- 客单价：372元
- 常购时段：周末下午、工作日晚8点后
- 优惠券使用率：68%"""

    try:
        profile: CustomerProfile = profile_chain.invoke({"customer_data": customer_data})
        print(f"  客户ID:       {profile.customer_id}")
        print(f"  RFM分群:      {profile.rfm_segment}")
        print(f"  偏好品类:     {', '.join(profile.consumption_preference)}")
        print(f"  购物习惯:     {profile.shopping_habit}")
        print(f"  营销策略:     {profile.marketing_strategy}")
        print(f"  预估ROI:      {profile.expected_roi}")
    except Exception as e:
        print(f"  [结构化输出失败: {e}]，降级为文本模式...")
        try:
            text_chain = prompt | llm | StrOutputParser()
            result = text_chain.invoke({"customer_data": customer_data})
            print(f"  {result[:400]}...")
        except Exception as e2:
            print(f"  [文本模式也失败: {e2}]")

    print("\n课题10完成！")


if __name__ == "__main__":
    exercise10_run()
