"""
课题15.5: 事件驱动Agent实战
三种触发模式 + System Hint + 模式对比
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, build_lcel_chain, DATA_DIR
from training_utils import EventDrivenAgent


def exercise15_5_run():
    print("=" * 60)
    print("课题15.5: 事件驱动Agent实战")
    print("  三种触发模式 + System Hint + 模式对比")
    print("=" * 60)

    llm = get_llm()

    # ==========================================
    # 步骤1: 搭建事件驱动架构
    # ==========================================
    print("\n--- 步骤1: 搭建事件驱动架构 ---")

    eda = EventDrivenAgent(name="区县运营智能体", client=None)
    print("  EventDrivenAgent实例创建成功")
    print(f"  架构说明: 事件源 → 事件总线 → 处理器 → 智能体推理 → 响应")

    # ==========================================
    # 步骤2: 实现三种触发模式
    # ==========================================
    print("\n--- 步骤2: 实现三种触发模式 ---")

    # 触发模式1: 定时触发
    print("\n[触发模式1] 定时触发：每天9:00商机跟进提醒")

    def handle_timer(event):
        task = event.data.get("task", "未指定任务")
        target = event.data.get("target", "未指定目标")
        print(f"  定时任务执行: {task}")
        print(f"  → 目标: {target}")
        print(f"  → 动作: 调用智能体生成跟进提醒并推送给客户经理")
        eda.add_todo(f"跟进 {target} 的商机", "high")

    eda.register_handler("timer", handle_timer)

    timer_event = EventDrivenAgent.Event(
        event_type="timer", source="cron-scheduler",
        data={"task": "商机跟进提醒", "target": "苏州XX电子有限公司", "scheduled_time": "09:00", "last_follow_up": "3天前"}
    )
    eda.emit_event(timer_event)

    # 触发模式2: 数据触发
    print("\n[触发模式2] 数据触发：缺陷率超阈值告警")

    def handle_data_alert(event):
        metric = event.data.get("metric", "未知指标")
        value = event.data.get("value", "0")
        threshold = event.data.get("threshold", "0")
        print(f"  数据异常检测: {metric} = {value}（阈值: {threshold}）")
        print(f"  → 动作: 自动触发根因分析 + 告警通知")
        eda.add_todo(f"处理{metric}超阈值告警", "high")

    eda.register_handler("data_alert", handle_data_alert)

    data_event = EventDrivenAgent.Event(
        event_type="data_alert", source="生产监控系统",
        data={"metric": "PCB板缺陷率", "value": "5.2%", "threshold": "3.0%",
              "production_line": "A3线", "trend": "连续3天上升"}
    )
    eda.emit_event(data_event)

    # 触发模式3: 外部触发
    print("\n[触发模式3] 外部触发：客户提交申请→启动审核")

    def handle_application(event):
        applicant = event.data.get("applicant", "未知客户")
        biz_type = event.data.get("business_type", "未知业务")
        print(f"  客户申请事件: {applicant} 申请 {biz_type}")
        print(f"  → 动作: 自动启动审核工作流")
        eda.add_todo(f"审核 {applicant} 的{biz_type}申请", "medium")

    eda.register_handler("external_application", handle_application)

    external_event = EventDrivenAgent.Event(
        event_type="external_application", source="客户自助平台",
        data={"applicant": "苏州XX科技有限公司", "business_type": "专线扩容", "amount": "50万"}
    )
    eda.emit_event(external_event)

    # ==========================================
    # 步骤3: 集成System Hint + LCEL Chain
    # ==========================================
    print("\n--- 步骤3: 集成System Hint + LCEL Chain ---")

    eda.update_system_hints()
    print(f"  System Hint当前状态:")
    for k, v in eda.system_hints.items():
        print(f"    {k}: {v}")

    print(f"\n  当前TODO列表 ({len(eda.todo_list)} 项):")
    for todo in eda.todo_list:
        status = "done" if todo["done"] else "pending"
        print(f"    [{todo['priority']}] {todo['task']} ({status})")

    # 构建 System Hint 文本
    todo_lines = [f"  - [{t['priority']}] {t['task']}" for t in eda.todo_list if not t['done']]
    hint_text = (
        f"[System Hint]\n"
        f"当前时间: {eda.system_hints.get('current_time', 'N/A')}\n"
        f"待办事项数: {eda.system_hints.get('todo_count', 0)}\n"
        f"待办清单:\n" + "\n".join(todo_lines)
    )

    print(f"\n  注入Prompt的System Hint片段:")
    print(f"  {hint_text[:200]}...")

    # 创建带System Hint的 LCEL Chain
    smart_chain = build_lcel_chain(
        "你是区县电信运营助手。\n"
        "你会收到System Hint信息，包含当前时间和待办清单。\n"
        "请根据System Hint主动提醒用户待办事项，而不是被动等待提问。\n\n"
        + hint_text,
        llm=llm,
    )
    print("\n  带System Hint的 LCEL Chain 创建完成")

    # 测试带Hint的Chain
    try:
        result = smart_chain.invoke({"input": "今天有什么需要我处理的事项吗？"})
        print(f"\n  智能体回复（主动提醒模式）:\n  {result[:200]}...")
    except Exception as e:
        print(f"\n  [调用失败: {e}]")

    # ==========================================
    # 步骤4: 对比被动模式 vs 事件驱动模式
    # ==========================================
    print("\n--- 步骤4: 对比被动模式 vs 事件驱动模式 ---")

    passive_chain = build_lcel_chain(
        "你是区县电信运营助手，回答用户关于运营的问题。",
        llm=llm,
    )

    try:
        passive_result = passive_chain.invoke({"input": "今天有什么需要我处理的事项吗？"})
        print(f"被动模式回复:\n  {passive_result[:200]}...")
    except Exception as e:
        print(f"[被动模式调用失败: {e}]")

    print("\n" + "=" * 60)
    print("被动模式 vs 事件驱动模式 对比")
    print("=" * 60)
    comparison = [
        ["维度", "被动模式", "事件驱动模式"],
        ["触发方式", "用户主动提问", "事件自动触发"],
        ["时间感知", "无，不知道当前时间", "有，System Hint注入时间戳"],
        ["任务感知", "无，不知道待办事项", "有，TODO列表自动注入"],
        ["主动性", "被动等待", "主动提醒+自动执行"],
        ["适用场景", "简单问答", "运营巡检+商机跟进+风险告警"],
        ["开发复杂度", "低", "中（需事件总线+处理器注册）"],
    ]
    for row in comparison:
        print(f"  {row[0]:<12} | {row[1]:<22} | {row[2]:<26}")

    print("\n关键洞察：")
    print("  1. 事件驱动模式让Agent从「工具」升级为「协作伙伴」")
    print("  2. System Hint是连接Agent与业务状态的桥梁")
    print("  3. 三种触发模式覆盖了90%的运营自动化场景")
    print("  4. LCEL Chain 让 System Hint 注入只需修改 system_prompt 内容")

    print("\n课题15.5完成！事件驱动Agent架构已搭建。")


if __name__ == "__main__":
    exercise15_5_run()
