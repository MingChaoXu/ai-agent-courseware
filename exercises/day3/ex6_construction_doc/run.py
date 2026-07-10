"""
课题6: 建筑/交通领域管理文件生成
=================================
使用ChatPromptTemplate通过doc_type变量支持多种公文文种，StrOutputParser输出。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, DATA_DIR

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def exercise6_run():
    print("=" * 60)
    print("课题6: 建筑/交通领域管理文件生成")
    print("=" * 60)

    llm = get_llm()

    print("\n--- 步骤1: 构建公文生成 LCEL Chain ---")
    print("""
公文生成 Chain 设计：
  - 一个 ChatPromptTemplate，通过 {doc_type} 变量支持多种文种
  - System Prompt 包含公文规范（语体、格式、结构）
  - 输出: StrOutputParser（公文为自由格式文本，不需结构化解析）
    """)

    doc_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个公文写作助手，帮助政府部门工作人员快速生成规范的公文。\n\n"
         "当前生成文种：{doc_type}\n\n"
         "支持的公文类型：\n"
         "1. 【通知】会议通知、工作通知、检查通知\n"
         "2. 【报告】工作汇报、情况报告、调研报告\n"
         "3. 【纪要】会议纪要、专题会议纪要\n\n"
         "公文规范：\n"
         "- 使用正式公文语体，不使用口语\n"
         "- 标题格式：发文机关+事由+文种\n"
         "- 正文结构完整：开头（目的/依据）+主体+结尾\n"
         "- 涉及时间、数字使用阿拉伯数字\n"
         "- 禁止使用「大概」「可能」等模糊表述\n\n"
         "输出时按公文格式排版，包含标题、主送机关、正文、落款。"),
        ("human", "{content}"),
    ])

    doc_chain = doc_prompt | llm | StrOutputParser()
    print("公文生成 Chain 构建完成")

    # 步骤2: 生成不同类型公文
    print("\n--- 步骤2: 生成公文测试 ---")

    print("\n生成【会议通知】")
    try:
        notice = doc_chain.invoke({
            "doc_type": "通知",
            "content": "请生成一份会议通知：关于召开2026年第三季度住建系统安全生产工作会议，时间7月15日上午9:00，地点市住建局会议室，参会人员为各区住建局分管领导。"
        })
        print(f"  {notice}")
    except Exception as e:
        print(f"  [生成失败: {e}]")

    print("\n生成【工作报告】")
    try:
        report = doc_chain.invoke({
            "doc_type": "报告",
            "content": "请生成一份情况报告：关于XX区老旧小区改造进展情况，已完成8个小区改造，惠及居民3200户，投资额1.2亿元，当前存在问题：部分小区居民配合度不高。"
        })
        print(f"  {report}")
    except Exception as e:
        print(f"  [生成失败: {e}]")

    print("\n课题6完成！")


if __name__ == "__main__":
    exercise6_run()
