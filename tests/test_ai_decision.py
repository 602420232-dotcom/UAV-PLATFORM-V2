"""
AI决策模块单元测试 - LLM辅助决策 + NLP任务解析 + 智能问答
"""
import logging
import os
import sys
import unittest

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'edge-cloud-coordinator'))

from ai_decision import (  # type: ignore[import-not-found]  # noqa: E402
    LLMAssistedDecision, SmartQASystem, NLPTask,
    IntentType
)


class TestLLMAssistedDecision(unittest.TestCase):
    """LLM辅助决策引擎测试"""

    def setUp(self):
        self.engine = LLMAssistedDecision()

    def test_initial_state(self):
        self.assertIsNotNone(self.engine)
        self.assertEqual(len(self.engine.conversation_history), 0)

    def test_understand_intent_path_planning(self):
        task = self.engine.understand_intent("规划从A点到B点的飞行路径")
        self.assertEqual(task.intent, IntentType.PATH_PLANNING)
        self.assertGreater(task.confidence, 0.5)

    def test_understand_intent_weather(self):
        task = self.engine.understand_intent("查询北京的天气情况")
        self.assertEqual(task.intent, IntentType.WEATHER_QUERY)
        self.assertGreater(task.confidence, 0.5)

    def test_understand_intent_drone_status(self):
        task = self.engine.understand_intent("查询无人机状态")
        self.assertEqual(task.intent, IntentType.DRONE_STATUS)

    def test_understand_intent_risk(self):
        task = self.engine.understand_intent("评估当前飞行安全性")
        self.assertEqual(task.intent, IntentType.RISK_ASSESSMENT)

    def test_suggest_decision_path_planning(self):
        task = self.engine.understand_intent("规划飞行路径")
        decision = self.engine.suggest_decision(task, {"drones": ["UAV-001"]})
        self.assertIn("response", decision)
        self.assertIn("action", decision)
        self.assertEqual(decision["action"], "path_planning")

    def test_suggest_decision_weather(self):
        task = self.engine.understand_intent("今天天气怎么样")
        decision = self.engine.suggest_decision(task, {})
        self.assertEqual(decision["action"], "weather_query")

    def test_chat_high_confidence(self):
        response = self.engine.chat("帮我规划一条飞行路径")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_chat_low_confidence(self):
        response = self.engine.chat("abcdef123xyz")
        self.assertIn("未能完全理解", response)

    def test_conversation_history(self):
        self.engine.chat("查询天气")
        self.engine.chat("无人机状态")
        self.assertGreaterEqual(len(self.engine.conversation_history), 2)


class TestSmartQASystem(unittest.TestCase):
    """智能问答系统测试"""

    def setUp(self):
        self.qa = SmartQASystem()

    def test_answer_existing(self):
        result = self.qa.answer("无人机最大飞行高度是多少")
        self.assertIn("150", result)

    def test_answer_unknown(self):
        result = self.qa.answer("完全不相关的内容")
        self.assertIn("暂无预设答案", result)

    def test_answer_empty(self):
        result = self.qa.answer("")
        self.assertIn("暂无预设答案", result)

    def test_answer_battery(self):
        result = self.qa.answer("电池续航多久")
        self.assertIn("25", result)


class TestNLPTask(unittest.TestCase):
    """NLP任务测试"""

    def test_task_creation(self):
        task = NLPTask(
            intent=IntentType.PATH_PLANNING,
            confidence=0.85,
            entities={"destination": "B区"},
            raw_text="飞到B区"
        )
        self.assertEqual(task.intent, IntentType.PATH_PLANNING)
        self.assertEqual(task.entities["destination"], "B区")
        self.assertEqual(task.raw_text, "飞到B区")


if __name__ == '__main__':
    unittest.main()
