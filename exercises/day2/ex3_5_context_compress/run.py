"""
课题3.5: 上下文压缩策略实验（LangChain Memory 对比）
=====================================================
- 步骤1: ConversationBufferMemory vs ConversationSummaryMemory
- 步骤2: 滑动窗口策略（手动实现最常用的压缩方法）
- 步骤3: 实战压缩策略选择指南
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryMemory

from shared_utils import get_llm, check_api_config


# ============================================================
#  课题3.5: 上下文压缩策略实验（LangChain Memory 对比）
# ============================================================

def exercise3_5_step1_memory_basics():
    """步骤1: LangChain Memory 基础 — Buffer vs Summary"""
    print("=" * 60)
    print("课题3.5: 上下文压缩策略实验")
    print("步骤1: ConversationBufferMemory vs ConversationSummaryMemory")
    print("=" * 60)
    print("""
为什么需要 Memory 管理？
  - LLM 上下文窗口有限（4K/8K/128K tokens）
  - 长对话中，历史消息逐渐占满窗口
  - Token 越多 → 延迟越高、成本越大
  - 不同 Memory 策略 = 不同的「压缩」方式

LangChain 两种核心 Memory：
  ① ConversationBufferMemory  — 保留完整历史（不压缩）
  ② ConversationSummaryMemory — LLM 自动摘要历史（压缩）
    """)

    from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryMemory

    llm = get_llm()

    # ---- Buffer Memory（完整记忆）----
    print("--- ConversationBufferMemory（不压缩，全部保留）---")
    buffer_memory = ConversationBufferMemory(return_messages=True)

    # 模拟对话
    conversation = [
        ("user", "我想咨询公积金提取的问题，我叫张明"),
        ("assistant", "张先生你好，公积金提取有多种情形，请问您是购房提取还是租房提取？"),
        ("user", "购房提取，我买了XX小区的房子，花了200万"),
        ("assistant", "购房提取需要提供购房合同、房产证、身份证等材料。"),
        ("user", "身份证号是320506199001011234，手机号13812345678"),
        ("assistant", "已记录您的身份信息。提取额度上限为账户余额，留10%保证金。"),
        ("user", "那社保转移怎么办理？需要多久？"),
        ("assistant", "社保转移可以通过国家社会保险公共服务平台线上办理，一般45个工作日完成。"),
        ("user", "好的，另外我还想问问新生儿落户的事"),
        ("assistant", "新生儿落户需要：出生医学证明、父母结婚证、户口簿、身份证。"),
    ]

    for role, content in conversation:
        if role == "user":
            buffer_memory.chat_memory.add_user_message(content)
        else:
            buffer_memory.chat_memory.add_ai_message(content)

    buffer_msgs = buffer_memory.load_memory_variables({})
    buffer_text = str(buffer_msgs.get("history", ""))
    buffer_chars = len(buffer_text)
    est_buffer_tokens = buffer_chars // 4

    print(f"  保留消息数: {len(buffer_memory.chat_memory.messages)}")
    print(f"  总字符数:   {buffer_chars}")
    print(f"  估计 Token: ~{est_buffer_tokens}")

    # ---- Summary Memory（摘要压缩）----
    print(f"\n--- ConversationSummaryMemory（LLM 自动摘要压缩）---")
    try:
        summary_memory = ConversationSummaryMemory(llm=llm, return_messages=True)

        # 逐条添加（Summary Memory 会自动在每轮生成摘要）
        for role, content in conversation:
            if role == "user":
                summary_memory.chat_memory.add_user_message(content)
            else:
                summary_memory.chat_memory.add_ai_message(content)

        # 手动触发摘要生成
        summary_memory.predict_new_summary(
            summary_memory.chat_memory.messages,
            summary_memory.moving_summary_buffer
        )

        summary_msgs = summary_memory.load_memory_variables({})
        summary_text = str(summary_msgs.get("history", ""))
        summary_chars = len(summary_text)
        est_summary_tokens = summary_chars // 4

        print(f"  摘要后字符数: {summary_chars}")
        print(f"  估计 Token:   ~{est_summary_tokens}")
        print(f"  压缩率:       {summary_chars / buffer_chars * 100:.0f}%")
        print(f"  摘要内容:     {summary_text[:200]}...")

    except Exception as e:
        print(f"  ⚠️ Summary Memory 生成失败: {e}")
        print("  模拟压缩结果: 压缩率约30-50%，保留关键信息（姓名、身份证、业务类别）")

    print(f"""
💡 对比：
  ┌─────────────────────┬──────────┬─────────────────────────┐
  │ 策略                 │ 压缩率   │ 特点                    │
  ├─────────────────────┼──────────┼─────────────────────────┤
  │ BufferMemory(不压缩) │ 100%     │ 信息完整，但Token消耗大  │
  │ SummaryMemory(摘要)  │ ~30-50%  │ 保留要点，细节可能丢失  │
  └─────────────────────┴──────────┴─────────────────────────┘
    """)


def exercise3_5_step2_sliding_window():
    """步骤2: 滑动窗口策略（手动实现最常用的压缩方法）"""
    print("\n" + "=" * 60)
    print("步骤2: 滑动窗口策略 — 只保留最近 K 轮对话")
    print("=" * 60)
    print("""
滑动窗口是最简单、最常用的上下文压缩方法：
  - 只保留最近 K 轮对话（K 通常为 3-5）
  - 超出窗口的历史直接丢弃
  - 零成本、零延迟、实现简单

在 LangChain 中的用法：
  直接在构建 messages 时，截取 history[-K*2:]（每轮2条消息）
    """)

    # 模拟对话历史
    history = [
        HumanMessage(content="我想咨询公积金提取的问题，我叫张明"),
        AIMessage(content="张先生你好，公积金提取有多种情形，请问您是购房提取还是租房提取？"),
        HumanMessage(content="购房提取，买了XX小区的房子"),
        AIMessage(content="购房提取需要提供购房合同、房产证、身份证等材料。"),
        HumanMessage(content="身份证号是320506199001011234"),
        AIMessage(content="已记录您的身份信息。提取额度上限为账户余额。"),
        HumanMessage(content="社保转移怎么办理？"),
        AIMessage(content="社保转移可线上办理，45个工作日完成。"),
        HumanMessage(content="新生儿落户需要什么？"),
        AIMessage(content="需要出生医学证明、结婚证、户口簿。"),
        HumanMessage(content="落户后医保怎么变更？"),
    ]

    for K in [2, 3, 5]:
        window = history[-(K * 2):]  # 每轮2条消息
        chars = sum(len(m.content) for m in window)
        total_chars = sum(len(m.content) for m in history)
        print(f"\n  K={K}（保留最近{K}轮）: {len(window)}条消息, {chars}字符, 压缩率{chars/total_chars*100:.0f}%")
        for m in window:
            role = "👤" if isinstance(m, HumanMessage) else "🤖"
            print(f"    {role} {m.content[:40]}...")

    print("""
💡 滑动窗口的优缺点：
  ✅ 实现简单，零成本，零延迟
  ✅ 最近对话最重要，窗口策略符合直觉
  ❌ 早期重要信息（如用户姓名、身份证）可能被丢弃
  ❌ 无法根据内容重要性动态调整

  → 实际应用中，常将「滑动窗口 + 系统提示中保留关键实体」结合使用
    """)


def exercise3_5_step3_practical_tips():
    """步骤3: 实战压缩策略选择指南"""
    print("\n" + "=" * 60)
    print("步骤3: 实战压缩策略选择指南")
    print("=" * 60)
    print("""
┌──────────────────────┬──────────┬────────────────────────────────┐
│ 策略                  │ 压缩率   │ 适用场景                        │
├──────────────────────┼──────────┼────────────────────────────────┤
│ 不压缩(Buffer)        │ 0%       │ 短对话(<10轮)，调试阶段         │
│ 滑动窗口(K=3)         │ ~60%     │ 通用场景，最简单有效            │
│ 摘要(Summary)         │ ~50%     │ 长对话，需保留要点              │
│ 摘要+引用             │ ~40%     │ 合规/法律场景，需可追溯         │
│ 分级保留              │ ~30%     │ 超长对话，分层级保留            │
└──────────────────────┴──────────┴────────────────────────────────┘

LangChain 实现方式：
  1) ConversationBufferMemory        → 不压缩
  2) 手动截取 history[-K*2:]          → 滑动窗口
  3) ConversationSummaryMemory       → LLM 摘要
  4) ConversationSummaryBufferMemory → 摘要+缓冲（近期不压缩，远期摘要）

生产环境推荐：
  - 默认：ConversationSummaryBufferMemory（兼顾近期完整+远期摘要）
  - 简单场景：滑动窗口（零成本，够用）
  - 合规场景：摘要+引用（所有关键信息可回溯）
    """)


def run_exercise3_5():
    """运行课题3.5完整流程"""
    exercise3_5_step1_memory_basics()
    exercise3_5_step2_sliding_window()
    exercise3_5_step3_practical_tips()
    print("\n✅ 课题3.5完成！你已掌握上下文压缩策略。")


if __name__ == "__main__":
    check_api_config()
    run_exercise3_5()
