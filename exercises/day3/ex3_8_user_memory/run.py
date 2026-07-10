"""
课题3.8: 用户记忆系统实验（原理层）
===================================
演示三种记忆架构，并用LCEL Chain对比有无记忆的对话质量。
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, DATA_DIR
from training_utils import MemoryManager

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def exercise38_run():
    print("=" * 60)
    print("课题3.8: 用户记忆系统实验")
    print("=" * 60)

    # 步骤1: 演示三种记忆架构
    print("\n--- 步骤1: 三种记忆架构对比 ---")

    print("\n架构1: 扁平笔记")
    flat_memory = []
    flat_memory.append({"content": "用户姓名：王主任", "timestamp": time.time()})
    flat_memory.append({"content": "负责领域：社会综合治理", "timestamp": time.time()})
    flat_memory.append({"content": "偏好：简报要求数据先行", "timestamp": time.time()})
    print("  存储格式: [{content, timestamp}, ...]")
    print(f"  示例: {flat_memory[0]}")
    print("  优缺点: 简单易实现 / 无结构化，检索效率低")

    print("\n架构2: JSON层级")
    json_memory = {
        "个人信息": {"姓名": "王主任", "职务": "综治中心主任"},
        "业务偏好": {"简报风格": "数据先行", "关注领域": "矛盾纠纷"},
        "交互记录": {"咨询次数": 5, "上次话题": "劳资纠纷处理"}
    }
    print("  存储格式: {category: {key: value, ...}, ...}")
    print(f"  示例: {json.dumps(json_memory, ensure_ascii=False, indent=2)}")
    print("  优缺点: 结构清晰 / 层级固定，扩展性差")

    print("\n架构3: 高级JSON卡片（MemoryManager）")
    mem_file = os.path.join(DATA_DIR, "memory_demo.json")
    os.makedirs(DATA_DIR, exist_ok=True)
    mm = MemoryManager(filepath=mem_file)
    mm.add_fact("个人信息", "姓名", "王主任")
    mm.add_fact("个人信息", "职务", "综治中心主任")
    mm.add_fact("业务偏好", "简报风格", "数据先行")
    mm.add_fact("业务偏好", "关注领域", "矛盾纠纷")
    mm.add_fact("交互记录", "咨询次数", "5次")
    mm.add_fact("交互记录", "上次话题", "劳资纠纷处理")
    print("  存储格式: [{category, key, value, timestamp, metadata}, ...]")
    for m in mm.memory:
        print(f"  [{m['category']}] {m['key']}: {m['value']}")
    print("  优缺点: 灵活可扩展 / 实现复杂度较高")

    # 步骤2: 政务场景实践 — 用 LCEL Chain 演示记忆注入
    print("\n--- 步骤2: 政务场景实践：记录→检索→注入Prompt ---")
    llm = get_llm()

    print("\n记录用户信息...")
    mm2 = MemoryManager(filepath=os.path.join(DATA_DIR, "gov_memory.json"))
    mm2.add_fact("用户画像", "部门", "XX区住建局", {"来源": "首次对话"})
    mm2.add_fact("用户画像", "负责业务", "老旧小区改造", {"来源": "首次对话"})
    mm2.add_fact("用户画像", "职级", "科室负责人", {"来源": "首次对话"})
    mm2.add_fact("工作偏好", "报告风格", "数据驱动、问题导向", {"来源": "对话推断"})
    mm2.add_fact("工作偏好", "常用文种", "通知、情况报告", {"来源": "对话推断"})
    mm2.add_fact("历史任务", "上次生成", "第三季度安全检查通知", {"来源": "交互记录"})
    print(f"  已记录 {len(mm2.memory)} 条记忆")

    print("\n检索与「报告」相关记忆...")
    results = mm2.search("报告")
    for r in results:
        print(f"  [{r['category']}] {r['key']}: {r['value']} (score={r['score']})")

    print("\n注入Prompt记忆上下文...")
    mem_context = mm2.get_context_for_prompt("老旧小区改造报告")
    print(f"  注入的记忆片段:\n{mem_context}")

    # ---- 用 LCEL 构建有记忆的 Chain ----
    print("\n构建 LCEL Chain（记忆增强版 vs 无记忆版）...")

    # 有记忆版 Chain
    prompt_with_mem = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个政务文件生成助手。\n\n"
         "{memory_context}\n\n"
         "根据以上用户记忆，个性化生成文件：\n"
         "- 匹配用户部门和工作领域\n"
         "- 采用用户偏好的文风和格式\n"
         "- 参考历史任务经验"),
        ("human", "{question}"),
    ])

    chain_with_mem = prompt_with_mem | llm | StrOutputParser()

    # 无记忆版 Chain
    prompt_no_mem = ChatPromptTemplate.from_messages([
        ("system", "你是一个政务文件生成助手，请根据用户需求生成文件。"),
        ("human", "{question}"),
    ])

    chain_no_mem = prompt_no_mem | llm | StrOutputParser()

    # 步骤3: 对比有无记忆的对话质量
    print("\n--- 步骤3: 对比有无记忆的对话质量差异 ---")

    test_prompt = "帮我写一份老旧小区改造进展报告"

    print(f"\n无记忆版回答:")
    try:
        no_mem_answer = chain_no_mem.invoke({"question": test_prompt})
        print(f"  {no_mem_answer[:300]}...")
    except Exception as e:
        print(f"  [调用失败: {e}]")

    print(f"\n有记忆版回答:")
    try:
        with_mem_answer = chain_with_mem.invoke({
            "question": test_prompt,
            "memory_context": mem_context,
        })
        print(f"  {with_mem_answer[:300]}...")
    except Exception as e:
        print(f"  [调用失败: {e}]")

    print("\n对比分析:")
    print("  ┌──────────┬────────────────┬────────────────┐")
    print("  │ 维度     │ 无记忆         │ 有记忆         │")
    print("  ├──────────┼────────────────┼────────────────┤")
    print("  │ 部门归属 │ 泛化（未知）   │ XX区住建局     │")
    print("  │ 文风匹配 │ 默认公文风     │ 数据驱动风     │")
    print("  │ 业务深度 │ 通用水准       │ 老旧小区专项   │")
    print("  │ 历史参考 │ 无             │ 参考上次任务   │")
    print("  └──────────┴────────────────┴────────────────┘")

    print("\n核心洞察:")
    print("  - 记忆系统让Agent从「通用工具」进化为「专属助手」")
    print("  - 三种架构选择: 轻量用扁平，业务用JSON层级，复杂用高级卡片")
    print("  - 记忆注入Prompt是最简单有效的上下文工程手段之一")
    print("  - LCEL Chain: prompt模板中 {memory_context} 占位符 → invoke时传入记忆内容")

    print("\n课题3.8完成！")


if __name__ == "__main__":
    exercise38_run()
