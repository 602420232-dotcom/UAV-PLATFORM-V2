"""
AI增强决策 - 大语言模型辅助决策 + 自然语言任务下达 + 智能问答系统
"""
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    PATH_PLANNING = "path_planning"
    WEATHER_QUERY = "weather_query"
    DRONE_STATUS = "drone_status"
    RISK_ASSESSMENT = "risk_assessment"
    MISSION_PLANNING = "mission_planning"
    SYSTEM_HEALTH = "system_health"


@dataclass
class NLPTask:
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    raw_text: str


class LLMAssistedDecision:
    """大语言模型辅助决策引擎"""

    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.conversation_history: List[dict] = []
        self.max_history = 20

    def understand_intent(self, user_input: str) -> NLPTask:
        """理解自然语言意图(关键词匹配+规则引擎)"""
        text = user_input.lower()
        entities = {}
        confidence = 0.0
        intent = IntentType.SYSTEM_HEALTH

        if any(kw in text for kw in ["规划", "路径", "航线", "飞行路线", "巡航"]):
            intent = IntentType.PATH_PLANNING
            confidence = 0.85
        elif any(kw in text for kw in ["天气", "气象", "风速", "能见度", "预报"]):
            intent = IntentType.WEATHER_QUERY
            confidence = 0.9
            import re
            locs = re.findall(r'(?:在|到|从|于)([\u4e00-\u9fa5]{2,6}(?:市|区|县|路|街道))', user_input)
            if locs:
                entities["location"] = locs
        elif any(kw in text for kw in ["无人机", "飞机", "状态", "位置", "电量"]):
            intent = IntentType.DRONE_STATUS
            confidence = 0.85
            ids = [w for w in text.split() if "uav" in w or "drone" in w or w.startswith("00")]
            if ids:
                entities["drone_ids"] = ids
        elif any(kw in text for kw in ["风险", "安全", "危险", "告警"]):
            intent = IntentType.RISK_ASSESSMENT
            confidence = 0.8
        elif any(kw in text for kw in ["任务", "下达", "指令", "执行", "起飞", "降落"]):
            intent = IntentType.MISSION_PLANNING
            confidence = 0.75
            if "起飞" in text:
                entities["action"] = "takeoff"
            elif "降落" in text:
                entities["action"] = "land"
            elif "返航" in text:
                entities["action"] = "return"

        return NLPTask(intent=intent, confidence=confidence, entities=entities, raw_text=user_input)

    def suggest_decision(self, task: NLPTask, system_context: dict) -> dict:
        """基于理解的任务生成决策建议"""
        self.conversation_history.append({"role": "user", "content": task.raw_text})
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        if task.intent == IntentType.PATH_PLANNING:
            return self._suggest_path_planning(task, system_context)
        elif task.intent == IntentType.WEATHER_QUERY:
            return self._suggest_weather_query(task, system_context)
        elif task.intent == IntentType.DRONE_STATUS:
            return self._suggest_drone_status(task, system_context)
        elif task.intent == IntentType.RISK_ASSESSMENT:
            return self._suggest_risk_assessment(task, system_context)
        elif task.intent == IntentType.MISSION_PLANNING:
            return self._suggest_mission_planning(task, system_context)
        else:
            return {"response": "已收到请求，正在处理中...", "confidence": task.confidence}

    def _suggest_path_planning(self, task: NLPTask, ctx: dict) -> dict:
        return {
            "response": "已理解路径规划请求: 正在计算最优航线...",
            "action": "path_planning",
            "params": {"drone_id": task.entities.get("drone_ids", ["UAV-001"])[0],
                       "optimization": "multi_objective",
                       "preferences": task.entities.get("preferences", {})}
        }

    def _suggest_weather_query(self, task: NLPTask, ctx: dict) -> dict:
        return {
            "response": "正在查询气象数据...",
            "action": "weather_query",
            "params": {"location": task.entities.get("location", ["北京"]),
                       "include_forecast": True}
        }

    def _suggest_drone_status(self, task: NLPTask, ctx: dict) -> dict:
        return {
            "response": "正在获取无人机状态...",
            "action": "drone_status",
            "params": {"drone_id": task.entities.get("drone_ids", ["UAV-001"])[0]}
        }

    def _suggest_risk_assessment(self, task: NLPTask, ctx: dict) -> dict:
        return {
            "response": "正在进行全面的风险评估...",
            "action": "risk_assessment",
            "params": {"scope": "all_drones", "include_weather": True}
        }

    def _suggest_mission_planning(self, task: NLPTask, ctx: dict) -> dict:
        action = task.entities.get("action", "unknown")
        return {
            "response": f"任务指令已确认: {action}",
            "action": "execute_mission",
            "params": {"command": action, "drone_id": "UAV-001"}
        }

    def chat(self, message: str, context: dict = None) -> str:
        """自然语言对话接口"""
        task = self.understand_intent(message)
        if task.confidence < 0.5:
            return f"未能完全理解您的请求(置信度:{task.confidence:.2f})，请更具体地描述"
        result = self.suggest_decision(task, context or {})
        self.conversation_history.append({"role": "assistant", "content": result["response"]})
        return result["response"]


class SmartQASystem:
    """智能问答系统"""

    def __init__(self):
        self.knowledge_base = self._init_knowledge_base()

    def _init_knowledge_base(self) -> Dict:
        return {
            "最大飞行高度": "150米(视距内)/300米(超视距需审批)",
            "最大风速": "10m/s(安全)/15m/s(极限)",
            "电池续航": "约25分钟(视负载和气象条件)",
            "禁飞区": "机场周边、军事区、政府机关、人口密集区",
            "如何规划路径": "系统支持VRPTW+DE-RRT*+DWA三层路径规划",
            "数据同化是什么": "贝叶斯数据同化融合多源气象观测数据提高预报精度"
        }

    def answer(self, question: str) -> str:
        """基于知识库的智能问答"""
        for keyword, answer in self.knowledge_base.items():
            if keyword in question:
                return answer
        return "该问题暂无预设答案，建议查阅系统文档或联系技术支持"
