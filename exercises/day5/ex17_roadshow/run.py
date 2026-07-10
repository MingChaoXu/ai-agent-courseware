"""
课题17: 综合方案路演准备
路演框架 + Demo搭建 + 评分体系
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, build_lcel_chain, DATA_DIR
from training_utils import EventDrivenAgent


def exercise17_run():
    print("=" * 60)
    print("课题17: 综合方案路演准备")
    print("  路演框架 + Demo搭建 + 评分体系")
    print("=" * 60)

    llm = get_llm()

    # ==========================================
    # 步骤1: 路演框架
    # ==========================================
    print("\n--- 步骤1: 路演框架 ---")

    roadshow_framework = {
        "1_场景分析": {
            "weight": "20%",
            "points": [
                "业务痛点描述（量化数据支撑）",
                "目标用户画像（客户经理/市民/网格员）",
                "ROI预期（效率提升/成本节约/收入增长）",
                "竞品对比（为什么AI方案优于传统方案）",
            ]
        },
        "2_技术方案": {
            "weight": "30%",
            "points": [
                "系统架构图（Agent拓扑 + 数据流 + 事件总线）",
                "核心技术选型（LLM/RAG/多Agent/事件驱动）",
                "创新点说明（与通用方案的区别）",
                "安全与合规（数据脱敏/权限控制/审计日志）",
            ]
        },
        "3_Demo演示": {
            "weight": "30%",
            "points": [
                "端到端业务流程演示（2-3个核心场景）",
                "事件触发演示（定时/数据/外部触发）",
                "异常处理演示（容错/降级/人工接管）",
                "效果对比（传统方式 vs AI方式）",
            ]
        },
        "4_商业价值": {
            "weight": "20%",
            "points": [
                "量化收益（人效提升XX%/响应时间降低XX%）",
                "推广路径（试点→区县→全市）",
                "商业模式（SaaS订阅/项目制/混合）",
                "二期规划（扩展场景/模型微调/生态接入）",
            ]
        }
    }

    print("  路演四大板块:")
    for section, detail in roadshow_framework.items():
        print(f"\n  {section}（权重: {detail['weight']}）")
        for p in detail["points"]:
            print(f"    - {p}")

    # ==========================================
    # 步骤2: 搭建完整Demo — LCEL Chain 编排
    # ==========================================
    print("\n--- 步骤2: 搭建完整Demo（LCEL Chain 编排） ---")

    print("\n  [Demo模块1] 创建政务全链路 Chain")
    demo_qa = build_lcel_chain(
        "你是政务大厅问答Agent。\n"
        "职责：理解市民诉求，判断业务类型并提取关键信息。\n"
        "业务类型：户籍办理 | 社保业务 | 公积金业务 | 不动产登记 | 婚姻登记 | 其他\n"
        "输出格式：JSON {\"intent\": \"业务类型\", \"keywords\": [\"关键词\"], \"urgency\": \"普通/加急\"}",
        llm=llm,
    )
    print("    问答Agent Chain 创建完成")

    demo_process = build_lcel_chain(
        "你是政务表单填写Agent。\n"
        "职责：根据用户提供的信息，自动填充业务表单。\n"
        "输出标准化JSON表单数据。",
        llm=llm,
    )
    print("    办理Agent Chain 创建完成")

    demo_review = build_lcel_chain(
        "你是政务业务审核Agent。\n"
        "审核规则：材料齐全→通过 | 存在问题→待补正 | 不符合政策→不通过\n"
        "输出：审核结论 + 受理编号 + 下一步指引",
        llm=llm,
    )
    print("    审核Agent Chain 创建完成")

    # 创建事件驱动的运营Agent
    print("\n  [Demo模块2] 创建事件驱动运营Agent")
    demo_eda = EventDrivenAgent(name="Demo-运营智能体", client=None)

    demo_eda.register_handler("timer", lambda e: print(f"    Demo: 定时触发 - {e.data.get('task', '')}"))
    demo_eda.register_handler("data_alert", lambda e: print(f"    Demo: 数据告警 - {e.data.get('metric', '')}超阈值"))
    demo_eda.register_handler("external_application", lambda e: print(f"    Demo: 外部申请 - {e.data.get('applicant', '')}"))
    print("    事件驱动Agent注册完成（3种事件类型）")

    # 搭建Demo工作流
    print("\n  [Demo模块3] Demo工作流（LCEL顺序调用）")

    def demo_workflow(user_message, user_info):
        """3步政务Demo工作流"""
        # Step 1
        try:
            intent = demo_qa.invoke({"input": user_message})
        except:
            intent = "{\"intent\": \"公积金业务\"}"
        # Step 2
        try:
            form = demo_process.invoke({"input": f"意图: {intent}\n用户信息: {json.dumps(user_info, ensure_ascii=False)}"})
        except:
            form = "表单填写失败"
        # Step 3
        try:
            review = demo_review.invoke({"input": form})
        except:
            review = "审核调用失败"
        return {"intent": intent, "form": form, "review": review}

    print("    Demo工作流: 问答→办理→审核（3步 LCEL Chain 顺序调用）")

    # Demo运行
    print("\n  [Demo运行] 模拟路演现场演示")
    print("  " + "-" * 40)

    print("\n  场景1: 市民公积金提取")
    demo_result = demo_workflow(
        "我想办理公积金提取，准备买房",
        {"name": "王明", "id_card": "320506199001011234", "phone": "13812345678"}
    )
    for step, output in demo_result.items():
        print(f"    {step}: {str(output)[:100]}...")

    print("\n  场景2: 事件触发演示")
    demo_eda.add_todo("跟进苏州XX公司商机", "high")
    demo_eda.update_system_hints()

    demo_eda.emit_event(EventDrivenAgent.Event(
        "timer", "cron", {"task": "商机跟进提醒", "target": "苏州XX公司"}
    ))
    demo_eda.emit_event(EventDrivenAgent.Event(
        "data_alert", "监控系统", {"metric": "缺陷率", "value": "5.2%", "threshold": "3%"}
    ))
    demo_eda.emit_event(EventDrivenAgent.Event(
        "external_application", "客户平台", {"applicant": "苏州XX科技", "business_type": "专线扩容"}
    ))

    # ==========================================
    # 步骤3: 评分维度与路演评分表
    # ==========================================
    print("\n--- 步骤3: 评分维度 ---")

    scoring_rubric = {
        "场景分析": {
            "weight": 20,
            "criteria": [
                ("业务痛点清晰，有量化数据", 5),
                ("目标用户画像准确", 5),
                ("ROI预期合理", 5),
                ("与竞品的差异化明确", 5),
            ]
        },
        "技术方案": {
            "weight": 30,
            "criteria": [
                ("架构图清晰完整", 8),
                ("技术选型有依据", 7),
                ("有创新点说明", 8),
                ("安全合规考虑周全", 7),
            ]
        },
        "Demo演示": {
            "weight": 30,
            "criteria": [
                ("端到端流程跑通", 8),
                ("事件触发功能演示", 7),
                ("异常处理有预案", 8),
                ("效果对比直观", 7),
            ]
        },
        "商业价值": {
            "weight": 20,
            "criteria": [
                ("量化收益可信", 6),
                ("推广路径可行", 5),
                ("商业模式清晰", 5),
                ("二期规划有远见", 4),
            ]
        }
    }

    print("  路演评分表:")
    total_max = 0
    for section, detail in scoring_rubric.items():
        section_max = sum(c[1] for c in detail["criteria"])
        total_max += section_max
        print(f"\n  {section}（权重{detail['weight']}%，满分{section_max}分）")
        for criterion, max_score in detail["criteria"]:
            print(f"    - {criterion}（满分{max_score}分）")

    print(f"\n  总分: 满分{total_max}分")
    print("  评级标准：")
    print(f"    优秀: >={int(total_max * 0.85)}分")
    print(f"    良好: >={int(total_max * 0.70)}分")
    print(f"    及格: >={int(total_max * 0.60)}分")

    # ==========================================
    # 步骤4: 路演准备Checklist
    # ==========================================
    print("\n--- 步骤4: 路演准备Checklist ---")

    checklist = {
        "场景分析": [
            "收集3个以上真实业务痛点案例",
            "量化传统方式的时间和成本",
            "明确AI方案的效率提升比例",
            "准备竞品对比表格",
        ],
        "技术方案": [
            "绘制系统架构图（含Agent拓扑）",
            "列出核心技术选型及理由",
            "提炼2-3个创新点",
            "准备安全合规说明",
        ],
        "Demo演示": [
            "端到端流程可正常运行",
            "事件触发功能已测试",
            "异常场景有兜底方案",
            "准备传统vs AI效果对比数据",
            "Demo数据已准备（避免现场用真实数据）",
        ],
        "商业价值": [
            "ROI计算模型已验证",
            "推广计划分3阶段",
            "商业模式已与业务方对齐",
            "二期规划有明确里程碑",
        ],
    }

    for section, items in checklist.items():
        print(f"\n  {section}:")
        for item in items:
            print(f"    [ ] {item}")

    print("\n路演Tips:")
    print("  1. 开场: 用一个痛点故事开场，30秒抓住注意力")
    print("  2. Demo: 提前录制备份视频，防止现场网络问题")
    print("  3. 互动: 准备2-3个互动问题让观众参与")
    print("  4. 收尾: 用一句话总结核心价值主张")
    print("  5. 代码: 用LCEL Chain编排，代码简洁透明，评审官一目了然")

    print("\n课题17完成！路演框架和Demo已准备就绪。")


if __name__ == "__main__":
    exercise17_run()
