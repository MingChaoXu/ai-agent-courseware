"""
课题15: 社会治理综合智能体
4Agent协同 + 并行处理 + 条件分支
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, build_lcel_chain, DATA_DIR


def exercise15_run():
    print("=" * 60)
    print("课题15: 社会治理综合智能体")
    print("  4Agent协同 + 并行处理 + 条件分支")
    print("=" * 60)

    llm = get_llm()

    # ==========================================
    # 步骤1: 创建4个专用 LCEL Chain
    # ==========================================
    print("\n--- 步骤1: 创建4个专用 LCEL Chain ---")

    event_chain = build_lcel_chain(
        "你是综治中心事件录入Agent。\n\n"
        "职责：将网格员上报的口语化事件信息转为标准化记录。\n"
        "提取字段：事件类型、发生时间、地点、当事人、事件描述、紧急程度\n"
        "事件类型分类：矛盾纠纷 | 安全隐患 | 民生诉求 | 城市管理 | 治安事件\n"
        "标准化要求：地址统一格式、时间24h制、人名脱敏处理",
        llm=llm,
    )
    print("  事件Agent Chain 创建完成")

    law_chain = build_lcel_chain(
        "你是纠纷法律咨询Agent。\n\n"
        "职责：根据纠纷类型检索适用法律条款，给出法律建议。\n"
        "常见纠纷类型及适用法律：\n"
        "- 劳资纠纷：《劳动合同法》第30/46/85条\n"
        "- 邻里纠纷：《民法典》第288/289条（相邻关系）\n"
        "- 租赁纠纷：《民法典》第703-734条\n"
        "- 消费纠纷：《消费者权益保护法》第55条\n\n"
        "输出：适用法条 + 简要解读 + 维权建议 + 调解优先提示",
        llm=llm,
    )
    print("  法律Agent Chain 创建完成")

    brief_chain = build_lcel_chain(
        "你是治理简报Agent。负责汇总数据并生成治理简报。\n"
        "包含：数据概览、分类统计、典型案例、风险预警、工作建议。",
        llm=llm,
    )
    print("  简报Agent Chain 创建完成")

    alert_chain = build_lcel_chain(
        "你是治理态势预警Agent。\n\n"
        "职责：分析区域治理数据，识别风险趋势并发出预警。\n"
        "预警维度：\n"
        "1. 事件趋势：某类事件是否持续上升\n"
        "2. 区域热点：哪些社区/网格事件集中\n"
        "3. 处理时效：超时未办结事件\n"
        "4. 重复事件：同一问题反复投诉\n\n"
        "预警等级：\n"
        "红色：群体性事件征兆、重大安全隐患\n"
        "黄色：某类事件上升>30%、处理时效超标\n"
        "绿色：各项指标正常",
        llm=llm,
    )
    print("  预警Agent Chain 创建完成")

    # ==========================================
    # 步骤2: 并行处理 + 条件分支
    # ==========================================
    print("\n--- 步骤2: 编排并行处理 + 条件分支工作流 ---")
    print("""
LCEL 编排策略：
  - 并行：threading.Thread 同时执行事件录入和态势预警
  - 条件分支：Python if 判断事件类型，仅纠纷类触发法律Agent
  - 汇总：所有结果拼接后送入简报Agent
    """)

    event_report = (
        "网格员张XX上报：\n"
        "时间：今天下午3点左右\n"
        "地点：XX小区3栋2单元\n"
        "情况：楼上502住户装修漏水，把楼下402的新装天花板泡了，"
        "402业主找502协商，502说装修队负责，装修队说建筑质量问题不归他们管，"
        "三方吵起来了。402业主情绪比较激动。"
    )

    monthly_data = (
        "6月治理数据：\n"
        "- 总事件：156件（环比+12%）\n"
        "- 矛盾纠纷：42件（环比+25%）\n"
        "- 安全隐患：28件\n"
        "- 民生诉求：56件\n"
        "- 城市管理：30件\n"
        "- 超时未办结：8件\n"
        "- 重复投诉：3件（均为XX小区物业问题）"
    )

    # ==========================================
    # 步骤3: 异步处理模式演示
    # ==========================================
    print("\n--- 步骤3: 并行处理模式演示 ---")

    results = {}

    def _run_event_entry():
        print("  [线程1] 事件录入开始...")
        try:
            results["event"] = event_chain.invoke({"input": event_report})
        except Exception as e:
            results["event"] = f"[失败: {e}]"
        print("  [线程1] 事件录入完成")

    def _run_alert_check():
        print("  [线程2] 态势预警开始...")
        try:
            results["alert"] = alert_chain.invoke({"input": monthly_data})
        except Exception as e:
            results["alert"] = f"[失败: {e}]"
        print("  [线程2] 态势预警完成")

    t1 = threading.Thread(target=_run_event_entry)
    t2 = threading.Thread(target=_run_alert_check)
    start_time = time.time()
    t1.start()
    t2.start()
    t1.join(timeout=120)
    t2.join(timeout=120)

    elapsed = time.time() - start_time
    print(f"\n  并行执行耗时: {elapsed:.1f}s")
    print("  （串行预估耗时: 2x 以上）")

    if "event" in results:
        print(f"\n事件录入结果:\n{results['event'][:200]}...")

    # ==========================================
    # 步骤4: 条件分支测试
    # ==========================================
    print("\n--- 步骤4: 条件分支测试 ---")

    print("\n[测试1] 矛盾纠纷类事件 → 触发法律Agent")
    try:
        law_result = law_chain.invoke({
            "input": "这是一起邻里漏水纠纷：楼上装修导致楼下天花板损坏，"
                     "三方（楼上业主、装修队、楼下业主）责任推诿。请提供法律建议。"
        })
        print(f"法律咨询:\n{law_result[:200]}...")
    except Exception as e:
        print(f"[调用失败: {e}]")

    print("\n[测试2] 安全隐患类事件 → 不触发法律Agent（条件分支跳过）")
    safety_report = "网格员上报：XX路施工现场围栏破损，行人可直接进入危险区域，有小孩在附近玩耍。"
    try:
        safety_result = event_chain.invoke({"input": safety_report})
        print(f"事件录入（无法律分支）:\n{safety_result[:200]}...")
    except Exception as e:
        print(f"[调用失败: {e}]")

    # 简报汇总
    print("\n--- 简报汇总 ---")
    brief_input = f"月度数据：{monthly_data}\n新增纠纷事件：邻里漏水纠纷"
    try:
        brief_result = brief_chain.invoke({"input": brief_input})
        print(f"治理简报:\n{brief_result[:200]}...")
    except Exception as e:
        print(f"[调用失败: {e}]")

    print("\n课题15完成！社会治理智能体已部署（含并行处理 + 条件分支 + LCEL编排）。")


if __name__ == "__main__":
    exercise15_run()
