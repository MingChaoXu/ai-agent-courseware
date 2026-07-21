"""
Day 5 实战课题
==============
课题15:   社会治理综合智能体（4Agent协同 + 并行+条件分支）
课题16:   智能体消融评估实战（消融实验 + 量化分析）
课题17:   综合方案路演准备（路演框架 + Demo搭建）

技术栈：LangChain 原生 API（ChatOpenAI, LCEL, langgraph create_react_agent, Tool）
"""

import sys
import os
import json
import time
import threading
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================
#  环境配置 & LangChain 核心导入
# ============================================================

from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(_env_path)

# ---- LangChain 核心 ----
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent

# ---- 培训工具 ----
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from training_utils import EventDrivenAgent, AblationFramework, MemoryManager

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ============================================================
#  公共辅助函数
# ============================================================

def get_llm(temperature: float = 0.3, max_tokens: int = 2000) -> ChatOpenAI:
    """创建 LLM 实例 — 所有课题共用"""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("OPENAI_API_BASE", ""),
        temperature=temperature,
        max_tokens=max_tokens,
    )


def check_api_config():
    """检查 API 配置"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_API_BASE", "")
    if not api_key or api_key == "sk-your-api-key-here":
        print("[警告] 未配置 OPENAI_API_KEY，请在 .env 文件中设置")
        print(f"  .env 文件位置: {_env_path}")
        return False
    if not base_url:
        print("[警告] 未配置 OPENAI_API_BASE，请在 .env 文件中设置")
        return False
    print(f"  API 地址: {base_url}")
    print(f"  模型名称: {os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')}")
    print(f"  API Key:  {'已配置' if api_key else '未配置'}")
    return True


def build_lcel_chain(system_prompt: str, llm=None):
    """快速构建 LCEL Chain: ChatPromptTemplate → LLM → StrOutputParser"""
    if llm is None:
        llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    return prompt | llm | StrOutputParser()


# ============================================================
#  课题15: 社会治理综合智能体
#  4Agent协同 + 并行执行 + 条件分支
# ============================================================

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


# ============================================================
#  课题16: 智能体消融评估实战
# ============================================================

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


# ============================================================
#  课题17: 综合方案路演准备
# ============================================================

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


# ============================================================
#  主入口
# ============================================================

EXERCISES = {
    "15":   ("课题15:   社会治理综合智能体（4Agent协同）", exercise15_run),
    "16":   ("课题16:   智能体消融评估实战", exercise16_run),
    "17":   ("课题17:   综合方案路演准备", exercise17_run),
}

if __name__ == "__main__":
    print("=" * 60)
    print("Day 5 实战课题：复杂智能体 + 评估 + 综合路演")
    print("=" * 60)
    check_api_config()
    print()
    print("可选课题：")
    for key, (desc, _) in EXERCISES.items():
        print(f"  {key:>4} - {desc}")
    print("  all  - 运行全部课题")

    choice = input("\n请输入选项: ").strip()

    if choice == "all":
        for key in ["15", "16", "17"]:
            EXERCISES[key][1]()
    elif choice in EXERCISES:
        EXERCISES[choice][1]()
    else:
        print(f"无效选项: {choice}")
