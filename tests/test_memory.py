"""
tests/test_memory.py

记忆模块单测：短期对话历史有界（只保留最近 max_messages 条）。
"""

import unittest

from agent.memory.history import ConversationHistory


class HistoryBoundTests(unittest.TestCase):

    def test_history_is_bounded(self):
        h = ConversationHistory(max_messages=4)
        for i in range(10):
            h.add_user(f"u{i}")
            h.add_assistant(f"a{i}")
        self.assertEqual(len(h.messages), 4)
        self.assertEqual(h.messages[-1]["content"], "a9")

    def test_from_dict_trims(self):
        h = ConversationHistory(max_messages=3)
        h.from_dict([{"role": "user", "content": str(i)} for i in range(8)])
        self.assertEqual(len(h.messages), 3)

    def test_get_window_returns_recent(self):
        h = ConversationHistory(max_messages=10)
        for i in range(5):
            h.add_user(f"u{i}")
        self.assertEqual([m["content"] for m in h.get_window(2)], ["u3", "u4"])


if __name__ == "__main__":
    unittest.main()
