"""
课题14: 政务服务全链路智能服务
5Agent协同 + System Hint机制 + 事件触发
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, build_lcel_chain, DATA_DIR
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from training_utils import EventDrivenAgent


def exercise14_run():
    print("=" * 60)
    print("课题14: 政务服务全链路智能服务")
    print("  5Agent协同 + System Hint机制 + 事件触发")
    print("=" * 60)

    llm = get_llm()

    # ==========================================
    # 步骤1: 构建5个专用 LCEL Chain
    # ==========================================
    print("\n--- 步骤1: 构建5个专用 LCEL Chain ---")
    print("""
多Agent编排策略（不用 workflow API，用 LCEL Chain 顺序调用）：
  1. 每个 Agent = 一个 LCEL Chain（system_prompt → llm → StrOutputParser）
  2. 上一个 Chain 的输出作为下一个 Chain 的输入
  3. System Hint 通过 system_prompt 中的模板变量注入

  对比 TeleAgentClient.create_agent + create_workflow：
  - LCEL: 每个 Agent 是一个 Python 函数，直接调用，参数传递透明
  - TeleAgent: Agent ID + workflow ID，调用过程封装在 client 内部
    """)

    # ---- System Hint 构建 ----
    def _build_system_hint(agent_name: str, extra: str = "") -> str:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        hint = (
            f"\n\n[System Hint]\n"
            f"当前时间: {current_time}\n"
            f"当前智能体: {agent_name}\n"
            f"已调用工具次数: 0\n"
            f"待办事项: 无\n"
        )
        if extra:
            hint += f"额外信息: {extra}\n"
        return hint

    # Agent 1: 问答理解
    qa_hint = _build_system_hint("政务问答Agent", "需判断6类业务类型")
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是政务大厅前台问答Agent。\n\n"
         "职责：理解市民诉求，判断业务类型并提取关键信息。\n"
         "业务类型：户籍办理 | 社保业务 | 公积金业务 | 不动产登记 | 婚姻登记 | 其他\n"
         "输出格式：JSON {\"intent\": \"业务类型\", \"keywords\": [\"关键词\"], \"urgency\": \"普通/加急\"}\n\n"
         "示例：\n"
         "用户：\"我想把户口从老家迁过来\"\n"
         "输出：{\"intent\": \"户籍办理\", \"keywords\": [\"户口迁移\", \"迁入\"], \"urgency\": \"普通\"}"
         + qa_hint),
        ("human", "{input}"),
    ])
    qa_chain = qa_prompt | llm | StrOutputParser()
    print("  问答Agent Chain 创建完成")

    # Agent 2: 推荐
    rec_hint = _build_system_hint("政务推荐Agent", "需推荐材料清单+办理渠道")
    rec_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是政务办事指南推荐Agent。\n\n"
         "职责：根据用户业务类型，推荐办理指南、所需材料、办理渠道。\n"
         "推荐内容：\n"
         "1. 所需材料清单（原件/复印件标注）\n"
         "2. 办理地点（线上/线下）\n"
         "3. 预计时长\n"
         "4. 费用\n"
         "5. 注意事项"
         + rec_hint),
        ("human", "{input}"),
    ])
    rec_chain = rec_prompt | llm | StrOutputParser()
    print("  推荐Agent Chain 创建完成")

    # Agent 3: 办理
    proc_hint = _build_system_hint("政务办理Agent", "需自动填充表单+格式校验")
    proc_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是政务表单填写Agent。\n\n"
         "职责：根据用户提供的信息，自动填充业务表单。\n"
         "处理规则：\n"
         "1. 将口语化信息转为规范表单字段\n"
         "2. 缺失字段明确列出，请用户补充\n"
         "3. 格式校验（身份证18位、手机号11位等）\n"
         "4. 输出标准化的表单数据JSON"
         + proc_hint),
        ("human", "{input}"),
    ])
    proc_chain = proc_prompt | llm | StrOutputParser()
    print("  办理Agent Chain 创建完成")

    # Agent 4: 校验
    ver_hint = _build_system_hint("政务校验Agent", "需检查4个维度")
    ver_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是政务材料校验Agent。\n\n"
         "职责：检查提交材料是否完整、合规。\n"
         "校验维度：\n"
         "1. 材料完整性：必收材料是否齐全\n"
         "2. 格式合规性：证件是否在有效期、复印件是否清晰\n"
         "3. 逻辑一致性：各材料信息是否一致（姓名、身份证号等）\n"
         "4. 政策符合性：是否符合当前政策要求"
         + ver_hint),
        ("human", "{input}"),
    ])
    ver_chain = ver_prompt | llm | StrOutputParser()
    print("  校验Agent Chain 创建完成")

    # Agent 5: 审核
    rev_hint = _build_system_hint("政务审核Agent", "需判定通过/待补正/不通过")
    rev_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是政务业务审核Agent。\n\n"
         "职责：对校验通过的业务进行审核判定。\n"
         "审核规则：\n"
         "1. 材料齐全且合规 → 审核通过，生成受理回执\n"
         "2. 存在可补正问题 → 审核待补正，列出补正清单\n"
         "3. 不符合政策 → 审核不通过，说明原因和政策依据\n\n"
         "输出：审核结论 + 受理编号 + 下一步指引"
         + rev_hint),
        ("human", "{input}"),
    ])
    rev_chain = rev_prompt | llm | StrOutputParser()
    print("  审核Agent Chain 创建完成")

    # ==========================================
    # 步骤2: 事件触发机制
    # ==========================================
    print("\n--- 步骤2: 搭建事件触发机制 ---")

    eda = EventDrivenAgent(name="政务服务事件网关", client=None)

    def on_application_submit(event):
        print(f"  收到申请事件: {event.data.get('applicant', '未知申请人')}")
        print("  → 自动启动政务全链路工作流")

    eda.register_handler("application_submitted", on_application_submit)

    def on_urgent_detect(event):
        print(f"  加急事件触发: {event.data}")
        print("  → 插入优先队列，跳过排队")

    eda.register_handler("urgent_detected", on_urgent_detect)

    eda.add_todo("处理用户公积金提取申请", "high")
    eda.add_todo("校验材料完整性", "medium")
    eda.add_todo("反馈审核结果", "medium")
    eda.update_system_hints()

    print(f"  事件处理器已注册: {list(eda.event_handlers.keys())}")
    print(f"  System Hint状态: {json.dumps(eda.system_hints, ensure_ascii=False)}")

    # ==========================================
    # 步骤3: 编排5步工作流（LCEL 顺序调用）
    # ==========================================
    print("\n--- 步骤3: 编排5步工作流（LCEL Chain 顺序调用） ---")
    print("""
LCEL 编排 vs TeleAgent workflow：
  TeleAgent: client.create_workflow(steps=[...]) → client.run_workflow(id, input)
  LCEL:      直接 Python 函数调用，上一个 Chain 输出传给下一个 Chain

  优势：
  - 透明：每步的输入输出完全可见
  - 灵活：可插入任意 Python 逻辑（条件分支、循环、异常处理）
  - 可调试：任何一步出错都能单独重试
    """)

    def run_gov_workflow(user_message: str, user_info: dict):
        """5步政务全链路工作流 — LCEL Chain 顺序编排"""
        results = {}

        # Step 1: 问答理解
        print("  [Step 1/5] 问答理解...")
        try:
            results["step1"] = qa_chain.invoke({"input": user_message})
        except Exception as e:
            results["step1"] = f"[调用失败: {e}]"
        print(f"    意图: {results['step1'][:100]}...")

        # Step 2: 办事推荐
        print("  [Step 2/5] 办事推荐...")
        try:
            results["step2"] = rec_chain.invoke({"input": results["step1"]})
        except Exception as e:
            results["step2"] = f"[调用失败: {e}]"
        print(f"    推荐: {results['step2'][:100]}...")

        # Step 3: 表单填写
        print("  [Step 3/5] 表单填写...")
        form_input = f"业务类型: {results['step1']}\n用户信息: {json.dumps(user_info, ensure_ascii=False)}"
        try:
            results["step3"] = proc_chain.invoke({"input": form_input})
        except Exception as e:
            results["step3"] = f"[调用失败: {e}]"
        print(f"    表单: {results['step3'][:100]}...")

        # Step 4: 材料校验
        print("  [Step 4/5] 材料校验...")
        try:
            results["step4"] = ver_chain.invoke({"input": results["step3"]})
        except Exception as e:
            results["step4"] = f"[调用失败: {e}]"
        print(f"    校验: {results['step4'][:100]}...")

        # Step 5: 业务审核
        print("  [Step 5/5] 业务审核...")
        review_input = f"表单: {results['step3']}\n校验: {results['step4']}"
        try:
            results["step5"] = rev_chain.invoke({"input": review_input})
        except Exception as e:
            results["step5"] = f"[调用失败: {e}]"
        print(f"    审核: {results['step5'][:100]}...")

        return results

    print("工作流编排完成: 问答→推荐→办理→校验→审核（5个 LCEL Chain 顺序调用）")

    # ==========================================
    # 步骤4: 事件触发+全链路测试
    # ==========================================
    print("\n--- 步骤4: 事件触发 + 全链路测试 ---")

    submit_event = EventDrivenAgent.Event(
        event_type="application_submitted",
        source="政务大厅自助终端",
        data={"applicant": "王明", "business_type": "公积金提取", "urgency": "普通"}
    )
    eda.emit_event(submit_event)

    test_input = {
        "user_message": "我想办理公积金提取，准备买房",
        "user_info": {
            "name": "王明",
            "id_card": "320506199001011234",
            "phone": "13812345678",
            "purpose": "购房提取",
        }
    }

    workflow_result = run_gov_workflow(test_input["user_message"], test_input["user_info"])

    print(f"\n全链路结果:")
    for step, output in workflow_result.items():
        print(f"  {step}: {output[:120]}...")

    # 模拟加急事件
    print("\n--- 加急事件测试 ---")
    urgent_event = EventDrivenAgent.Event(
        event_type="urgent_detected",
        source="系统自动检测",
        data={"reason": "军属优先", "applicant": "李军"}
    )
    eda.emit_event(urgent_event)

    print("\n课题14完成！政务全链路智能服务已部署（含System Hint + 事件触发 + LCEL编排）。")


if __name__ == "__main__":
    exercise14_run()
