"""课题7.5: Prompt消融实验（原理层）"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def exercise75_run():
    print("=" * 60)
    print("课题7.5: Prompt消融实验")
    print("=" * 60)

    # 步骤1: 消融实验方法论
    print("\n--- 步骤1: 消融实验方法论 ---")
    print("""
消融实验（Ablation Study）是Prompt工程的核心评估方法：
  原理：逐个移除Prompt组件，观察输出质量变化，量化各组件贡献度

  典型Prompt组件：
  ┌──────────────────────────────────────┐
  │ System Prompt（系统提示）             │  角色定义、行为约束
  │ Few-shot Examples（少样本示例）       │  输出格式参照
  │ Tool Descriptions（工具描述）         │  工具选择依据
  │ Reasoning Chain（推理链引导）         │  复杂推理能力
  │ Tone/Style（语气风格）               │  输出语气控制
  └──────────────────────────────────────┘

  消融实验步骤：
  1. 建立Baseline（完整Prompt配置）
  2. 逐个移除组件，记录输出变化
  3. 用评估函数量化差异
  4. 排序各组件贡献度
    """)

    # 步骤2: 合同审核场景消融实践 — 用 LCEL Chain
    print("\n--- 步骤2: 合同审核场景消融实践 ---")

    test_contract = "贷款合同：金额300万元，年利率浮动（银行可单方面调整），担保方式为企业资产整体抵押（未评估），违约金为贷款总额的8%，银行可随时要求提前还款。"

    # 定义不同Prompt配置 → 不同的 LCEL Chain
    prompt_configs = {
        "baseline": {
            "label": "完整配置（Baseline）",
            "system_prompt": (
                "你是一个专业的金融合同审核助手。\n\n"
                "审核维度：\n"
                "1. 利率条款风险\n"
                "2. 担保条款风险\n"
                "3. 违约条款风险\n"
                "4. 权利平衡性\n\n"
                "输出格式：\n"
                "风险等级 | 风险条款数 | 详细审核意见 | 修改建议"
            ),
        },
        "no_system_prompt": {
            "label": "移除系统提示",
            "system_prompt": "请审核以下合同。",
        },
        "no_tool_description": {
            "label": "移除审核维度指引",
            "system_prompt": "你是一个合同审核助手。\n\n请审核合同。（无审核维度指引）",
        },
        "informal_tone": {
            "label": "改为非正式语气",
            "system_prompt": (
                "嘿！来帮我看看这个合同有没有坑哈～\n\n"
                "大概看看这几点就行：\n"
                "- 利率有问题不\n"
                "- 担保靠谱不\n"
                "- 违约金离谱不\n"
                "- 有没有特别霸王的地方\n\n"
                "随便说说就好，不用太正式～"
            ),
        },
    }

    llm = get_llm()
    results_cache = {}

    # 为每种配置创建不同的 LCEL Chain
    print("构建4个不同配置的 LCEL Chain...")

    def build_chain(system_prompt: str):
        """根据系统提示构建 LCEL Chain"""
        p = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}"),
        ])
        return p | llm | StrOutputParser()

    def evaluate_contract_review(question, answer):
        score = 0.0
        if not answer or len(answer) < 20:
            return 0.0
        risk_keywords = ["风险", "违约", "担保", "利率", "霸王", "不合规", "违规", "建议修改", "条款"]
        found = sum(1 for kw in risk_keywords if kw in answer)
        score += found / len(risk_keywords) * 0.6
        structure_keywords = ["|", "1.", "2.", "3.", "4.", "报告", "审核"]
        found_struct = sum(1 for kw in structure_keywords if kw in answer)
        score += found_struct / len(structure_keywords) * 0.2
        score += min(0.2, len(answer) / 1000)
        return round(min(1.0, score), 3)

    questions = [f"请审核以下合同并给出专业审核意见：\n{test_contract}"]

    print("开始消融实验...\n")

    all_mode_results = []
    mode_names = ["baseline", "no_system_prompt", "no_tool_description", "informal_tone"]

    for mode in mode_names:
        config = prompt_configs[mode]
        chain = build_chain(config["system_prompt"])
        scores = []
        for q in questions:
            try:
                answer = chain.invoke({"question": q})
                results_cache[mode] = answer
                score = evaluate_contract_review(q, answer)
                scores.append(score)
            except Exception as e:
                print(f"  [配置 {mode} 调用失败: {e}]")
                scores.append(0.0)

        avg = sum(scores) / len(scores) if scores else 0
        all_mode_results.append({
            "mode": mode,
            "label": config["label"],
            "avg_score": avg,
        })
        answer_preview = results_cache.get(mode, "")[:150].replace("\n", " ")
        print(f"  {config['label']}")
        print(f"     得分: {avg:.3f} | 回答预览: {answer_preview}...")

    # 步骤3: 量化评估
    print("\n--- 步骤3: 量化评估结果 ---")
    baseline_score = all_mode_results[0]["avg_score"] if all_mode_results else 0

    print(f"\n{'配置':<25} {'得分':>8} {'变化':>10}")
    print("-" * 50)
    for r in all_mode_results:
        delta = r["avg_score"] - baseline_score
        delta_str = f"{'+' if delta >= 0 else ''}{delta:.3f}"
        marker = "  baseline" if r["mode"] == "baseline" else ""
        bar = "#" * int(r["avg_score"] * 20)
        print(f"{r['label']:<25} {r['avg_score']:>8.3f} {delta_str:>10}{marker}")
        print(f"{'':>25} {bar}")

    print("\n消融实验洞察:")
    print("  - 系统提示贡献最大 → 定义了角色、审核维度、输出格式")
    print("  - 审核维度指引影响显著 → 没有指引则审核零散无体系")
    print("  - 语气风格影响中等 → 非正式语气导致输出不专业")
    print("  - Baseline配置综合最优 → 各组件协同效果 > 单组件之和")

    print("\n实践建议:")
    print("  - 做Prompt优化时，先用消融实验定位最关键组件")
    print("  - 系统提示是最值得投入优化时间的部分")
    print("  - 语气风格虽影响不大，但在正式场景不可或缺")
    print("  - LCEL Chain 让消融实验变得简单：只需替换 system_prompt 部分")

    print("\n课题7.5完成！")


if __name__ == "__main__":
    exercise75_run()
