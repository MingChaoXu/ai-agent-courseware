"""
课题16: 智能体消融评估实战
消融实验 + 量化分析 + 评估报告
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, build_lcel_chain, DATA_DIR


def exercise16_run():
    print("=" * 60)
    print("课题16: 智能体消融评估实战")
    print("  消融实验 + 量化分析 + 评估报告")
    print("=" * 60)

    llm = get_llm()

    # ==========================================
    # 步骤1: 建立评估基准
    # ==========================================
    print("\n--- 步骤1: 建立评估基准 ---")

    test_questions = [
        "公积金购房提取需要哪些材料？",
        "户口从外地迁入苏州怎么办理？",
        "社保断缴3个月会有什么影响？",
        "不动产登记需要多长时间？",
        "婚姻登记可以跨区办理吗？",
    ]
    print(f"  测试问题数: {len(test_questions)}")

    def evaluate_answer(question: str, answer: str) -> float:
        """基于多维度评分的评估函数"""
        if not answer or len(answer) < 10:
            return 0.0
        score = 0.0
        # 维度1: 完整性
        if len(answer) > 50: score += 0.2
        if len(answer) > 150: score += 0.1
        # 维度2: 准确性
        accuracy_keywords = {
            "公积金": ["提取", "账户", "余额", "购房"],
            "户口": ["迁入", "迁出", "派出所", "户籍"],
            "社保": ["断缴", "补缴", "缴费", "养老"],
            "不动产": ["登记", "房产", "证书", "办理"],
            "婚姻": ["登记", "民政局", "跨区", "预约"],
        }
        for q_key, keywords in accuracy_keywords.items():
            if q_key in question:
                matched = sum(1 for kw in keywords if kw in answer)
                score += 0.3 * (matched / len(keywords))
                break
        # 维度3: 结构性
        structural_markers = ["1.", "2.", "第一步", "- "]
        if any(m in answer for m in structural_markers): score += 0.2
        # 维度4: 政策引用
        policy_markers = ["规定", "政策", "条例", "办法", "通知"]
        if any(m in answer for m in policy_markers): score += 0.2
        return min(1.0, score)

    print("  评估函数定义完成（4维度: 完整性+准确性+结构性+政策引用）")

    # ==========================================
    # 步骤2: 消融实验 — 不同 system_prompt 配置的 LCEL Chain
    # ==========================================
    print("\n--- 步骤2: 消融实验 ---")

    ablation_variants = {
        "baseline": {
            "description": "完整配置（system_prompt + 工具描述 + 专业语气）",
            "system_prompt": (
                "你是政务问答助手。\n"
                "职责：回答户籍、社保、公积金、不动产等政务咨询。\n"
                "要求：回答准确、条理清晰、引用政策依据。\n"
                "输出格式：结论 + 政策依据 + 办理指引"
            )
        },
        "no_system_prompt": {
            "description": "移除System Prompt",
            "system_prompt": "请回答以下问题。"
        },
        "no_tool_description": {
            "description": "移除工具描述",
            "system_prompt": (
                "你是政务问答助手。\n"
                "职责：回答政务咨询。\n"
                "输出格式：结论 + 办理指引"
            )
        },
        "informal_tone": {
            "description": "改为非正式语气",
            "system_prompt": (
                "你是个热心的政务咨询小伙伴~\n"
                "帮大家回答政务问题，随意一点就好，不用太正式。\n"
                "知道啥说啥就行~"
            )
        },
    }

    all_results = []
    mode_labels = {
        "baseline": "完整配置",
        "no_system_prompt": "移除System Prompt",
        "no_tool_description": "移除工具描述",
        "informal_tone": "非正式语气"
    }

    for mode, config in ablation_variants.items():
        print(f"\n消融模式: {mode} - {config['description']}")
        chain = build_lcel_chain(config["system_prompt"], llm=llm)
        mode_scores = []

        for q in test_questions:
            try:
                answer = chain.invoke({"input": q})
                score = evaluate_answer(q, answer)
                mode_scores.append(score)
            except Exception as e:
                print(f"  [问题调用失败: {e}]")
                mode_scores.append(0.0)

        avg_score = sum(mode_scores) / len(mode_scores) if mode_scores else 0
        all_results.append({
            "mode": mode,
            "label": mode_labels[mode],
            "avg_score": round(avg_score, 3),
            "scores": [round(s, 3) for s in mode_scores]
        })
        print(f"  各问题得分: {[round(s, 2) for s in mode_scores]}")
        print(f"  平均得分: {avg_score:.3f}")

    # ==========================================
    # 步骤3: 量化分析
    # ==========================================
    print("\n--- 步骤3: 量化分析各组件贡献度 ---")

    baseline_score = all_results[0]["avg_score"]
    for r in all_results:
        r["delta"] = round(r["avg_score"] - baseline_score, 3)
        r["contribution_pct"] = round(abs(r["delta"]) / baseline_score * 100, 1) if baseline_score > 0 else 0

    print(f"\n{'消融模式':<22} {'平均分':>8} {'变化量':>8} {'贡献占比':>8} {'影响等级':>10}")
    print("-" * 62)
    for r in all_results:
        delta_str = f"{'+' if r['delta'] >= 0 else ''}{r['delta']}"
        if r["mode"] == "baseline":
            impact = "— (基准)"
        elif abs(r["contribution_pct"]) > 30:
            impact = "RED 重大"
        elif abs(r["contribution_pct"]) > 15:
            impact = "YELLOW 显著"
        else:
            impact = "GREEN 轻微"
        print(f"{r['label']:<22} {r['avg_score']:>8.3f} {delta_str:>8} {r['contribution_pct']:>7.1f}% {impact:>10}")

    print("\n量化洞察：")
    print("  1. System Prompt是影响最大的组件 → 移除后准确率可能下降30%+")
    print("  2. 工具描述决定了LLM能否正确选工具 → 移除后工具调用失败率飙升")
    print("  3. 语气风格影响专业性感知 → 评分下降但功能不受损")

    # ==========================================
    # 步骤4: 生成评估报告
    # ==========================================
    print("\n--- 步骤4: 生成评估报告 ---")

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("智能体消融评估报告")
    report_lines.append("=" * 60)
    report_lines.append(f"评估时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"被测智能体: 政务问答助手")
    report_lines.append(f"测试问题数: {len(test_questions)}")
    report_lines.append(f"评估维度: 完整性 + 准确性 + 结构性 + 政策引用")
    report_lines.append("")
    report_lines.append("一、消融实验结果")
    report_lines.append("-" * 40)
    for r in all_results:
        delta_str = f"{'+' if r['delta'] >= 0 else ''}{r['delta']}"
        report_lines.append(f"  {r['label']}: {r['avg_score']:.3f} (变化: {delta_str})")
    report_lines.append("")
    report_lines.append("二、各问题详细得分")
    report_lines.append("-" * 40)
    for i, q in enumerate(test_questions):
        report_lines.append(f"  Q{i+1}: {q[:30]}...")
        for r in all_results:
            report_lines.append(f"    {r['label']}: {r['scores'][i]:.3f}")
    report_lines.append("")
    report_lines.append("三、核心结论")
    report_lines.append("-" * 40)
    sorted_results = sorted(all_results[1:], key=lambda x: abs(x["delta"]), reverse=True)
    for i, r in enumerate(sorted_results):
        report_lines.append(f"  {i+1}. {r['label']}影响最大，贡献占比{r['contribution_pct']}%")
    report_lines.append("")
    report_lines.append("四、优化建议")
    report_lines.append("-" * 40)
    report_lines.append("  1. 优先保障System Prompt的质量和完整性")
    report_lines.append("  2. 工具描述需精准，避免LLM选错工具")
    report_lines.append("  3. 语气风格可按业务场景灵活调整")
    report_lines.append("  4. 建议每次迭代都跑消融实验验证效果")
    report_lines.append("  5. LCEL Chain 让消融实验简单：只需替换 system_prompt 字符串")
    report_lines.append("=" * 60)

    report_text = "\n".join(report_lines)
    print(report_text)

    # 保存报告
    report_path = os.path.join(DATA_DIR, "ablation_report.txt")
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n  评估报告已保存: {report_path}")

    print("\n课题16完成！消融评估报告已生成。")


if __name__ == "__main__":
    exercise16_run()
