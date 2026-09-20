"""
agent/memory/turn.py

对话轮次记录（Turn Record）的组装：
把一轮的「用户输入 + AI 最终回复」聚合成一份结构化记录，供记忆更新消费。
"""


def build_turn_record(user_input, ai_reply):
    """
    组装一份轮次记录。

    Args:
        user_input: 用户本轮输入
        ai_reply: AI 本轮最终回复

    Returns:
        dict: {"user_input", "ai_reply"}
    """
    return {
        "user_input": user_input,
        "ai_reply": ai_reply,
    }
