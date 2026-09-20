"""
agent/memory/history.py

短期记忆容器：只存/取 user/assistant 最终对话，且**有界**——只保留最近 max_messages 条。
（发送与落盘都只取 `get_window`，更早的对话无需驻留内存。）
"""

# 默认保留条数（与 agent 的发送窗口一致）
DEFAULT_MAX_MESSAGES = 10


class ConversationHistory:

    def __init__(self, max_messages: int = DEFAULT_MAX_MESSAGES):
        self.max_messages = max_messages
        self.messages = []

    def _trim(self):
        """超出上限时丢弃最早的，保持有界。"""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def add_user(self, content):
        """追加一条 user 消息。"""
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant(self, content):
        """追加一条 assistant 消息。"""
        self.messages.append({"role": "assistant", "content": content})
        self._trim()

    def get_window(self, n):
        """返回最近 n 条历史（发送时用）；不足 n 条则全返回。"""
        return self.messages[-n:]

    def from_dict(self, messages):
        """恢复历史（供会话持久化加载），恢复后同样有界。"""
        self.messages = list(messages or [])
        self._trim()
