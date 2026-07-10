"""课题8: 社会治理领域治理简报生成"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field


class GovernanceBriefing(BaseModel):
    """治理简报结构化输出"""
    title: str = Field(description="简报标题")
    data_overview: str = Field(description="数据概览：事件总数、办结率、处理时长")
    key_work: str = Field(description="重点工作分类汇总")
    typical_cases: str = Field(description="典型案例（2-3个）")
    risk_warning: str = Field(description="风险预警")
    next_steps: str = Field(description="下步计划")


def exercise8_run():
    print("=" * 60)
    print("课题8: 社会治理领域治理简报生成")
    print("=" * 60)

    llm = get_llm()

    print("\n--- 步骤1: 构建治理简报 LCEL Chain ---")
    print("""
治理简报 Chain：
  ChatPromptTemplate → ChatOpenAI → PydanticOutputParser(GovernanceBriefing)
  输出为结构化简报对象，各字段可直接访问
    """)

    parser = PydanticOutputParser(pydantic_object=GovernanceBriefing)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个社会治理简报生成助手，帮助综治中心工作人员快速生成治理工作简报。\n\n"
         "简报规范：\n"
         "1. 标题：XX区XX街道社会治理工作简报（第X期）\n"
         "2. 数据概览：事件总数、已办结数、办结率、平均处理时长\n"
         "3. 重点工作：按类别分类汇总（矛盾纠纷、安全隐患、民生诉求、城市管理）\n"
         "4. 典型案例：选取2-3个代表性事件\n"
         "5. 风险预警：本月需关注的重点问题\n"
         "6. 下步计划：针对性措施建议\n\n"
         "语言要求：简明扼要，数据准确，突出重点。\n\n"
         "{format_instructions}"),
        ("human", "请根据以下数据生成治理简报：\n{monthly_data}"),
    ])

    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    briefing_chain = prompt | llm | parser
    print("治理简报 Chain 构建完成")

    # 步骤2: 生成简报
    print("\n--- 步骤2: 生成治理简报 ---")
    monthly_data = """
2026年6月XX街道社会治理数据：
- 事件总数：156件（较上月下降8%）
- 已办结：148件，办结率94.9%
- 平均处理时长：2.3天

分类统计：
- 矛盾纠纷：32件（邻里纠纷18件、劳资纠纷9件、其他5件）
- 安全隐患：45件（消防隐患22件、建筑安全13件、其他10件）
- 民生诉求：52件（环境投诉28件、市政设施15件、其他9件）
- 城市管理：27件（违建12件、占道经营9件、其他6件）

典型案例：
1. XX小区消防通道长期被占用，经协调物业设置隔离桩并加强巡查，已整改
2. XX路沿线商铺占道经营反复投诉，联合城管开展专项整治，暂有成效

重点关注：劳资纠纷较上月上升50%，主要涉及3家小企业欠薪问题"""

    try:
        briefing: GovernanceBriefing = briefing_chain.invoke({"monthly_data": monthly_data})
        print(f"  标题:     {briefing.title}")
        print(f"  数据概览: {briefing.data_overview[:100]}...")
        print(f"  重点工作: {briefing.key_work[:100]}...")
        print(f"  典型案例: {briefing.typical_cases[:100]}...")
        print(f"  风险预警: {briefing.risk_warning[:100]}...")
        print(f"  下步计划: {briefing.next_steps[:100]}...")
    except Exception as e:
        print(f"  [结构化输出失败: {e}]，降级为文本模式...")
        try:
            text_chain = prompt | llm | StrOutputParser()
            result = text_chain.invoke({"monthly_data": monthly_data})
            print(f"  {result}")
        except Exception as e2:
            print(f"  [文本模式也失败: {e2}]")

    print("\n课题8完成！")


if __name__ == "__main__":
    exercise8_run()
