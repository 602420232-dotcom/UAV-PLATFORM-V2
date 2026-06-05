"""
气象+路径知识图谱
语义增强搜索和推理，智能推荐引擎
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    id: str
    name: str
    type: str
    properties: dict
    embedding: List[float] = None


@dataclass
class Relation:
    source: str
    target: str
    relation_type: str
    weight: float = 1.0
    properties: dict = None


class KnowledgeGraph:
    """气象+路径知识图谱"""

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.entity_index = {}  # type -> [entity_ids]
        self._build_base_knowledge()

    def _build_base_knowledge(self):
        """构建基础气象知识"""
        weather_types = [
            {'id': 'w_calm', 'name': '静风', 'hazard': 0, 'speed': (0, 3)},
            {'id': 'w_breeze', 'name': '微风', 'hazard': 1, 'speed': (3, 6)},
            {'id': 'w_moderate', 'name': '和风', 'hazard': 2, 'speed': (6, 10)},
            {'id': 'w_strong', 'name': '强风', 'hazard': 3, 'speed': (10, 15)},
            {'id': 'w_gale', 'name': '大风', 'hazard': 4, 'speed': (15, 20)},
            {'id': 'w_storm', 'name': '风暴', 'hazard': 5, 'speed': (20, 50)}
        ]
        for wt in weather_types:
            self.add_entity(Entity(id=wt['id'], name=wt['name'],
                                   type='weather', properties=wt))

        terrain_types = [
            {'id': 't_urban', 'name': '城市', 'risk': 3, 'altitude': (0, 100)},
            {'id': 't_mountain', 'name': '山地', 'risk': 4, 'altitude': (500, 3000)},
            {'id': 't_water', 'name': '水域', 'risk': 2, 'altitude': (0, 0)},
            {'id': 't_plain', 'name': '平原', 'risk': 1, 'altitude': (0, 200)},
            {'id': 't_forest', 'name': '森林', 'risk': 2, 'altitude': (0, 500)}
        ]
        for t in terrain_types:
            self.add_entity(Entity(id=t['id'], name=t['name'],
                                   type='terrain', properties=t))

        # 气象→风险关系
        self.add_relation(Relation('w_gale', None, 'prohibits_flight', 1.0))
        self.add_relation(Relation('w_storm', None, 'prohibits_flight', 1.0))
        self.add_relation(Relation('w_strong', None, 'requires_caution', 0.7))
        self.add_relation(Relation('t_mountain', 'w_strong', 'combined_risk', 0.9))
        self.add_relation(Relation('t_urban', 'w_breeze', 'reduced_visibility', 0.3))

    def add_entity(self, entity: Entity):
        self.entities[entity.id] = entity
        if entity.type not in self.entity_index:
            self.entity_index[entity.type] = []
        self.entity_index[entity.type].append(entity.id)

    def add_relation(self, relation: Relation):
        self.relations.append(relation)

    def search(self, query: str, entity_type: Optional[str] = None) -> List[Entity]:
        """语义搜索"""
        query = query.lower()
        results = []
        candidates = self.entities.values()
        if entity_type and entity_type in self.entity_index:
            candidates = [self.entities[eid] for eid in self.entity_index[entity_type]]

        for entity in candidates:
            if query in entity.name.lower() or query in entity.id.lower():
                results.append(entity)
            for v in entity.properties.values():
                if isinstance(v, str) and query in v.lower():
                    results.append(entity)
                    break
        return results[:10]

    def reason(self, conditions: dict) -> List[dict]:
        """基于规则的推理"""
        wind_speed = conditions.get('wind_speed', 0)
        terrain = conditions.get('terrain', 'plain')

        inferences = []
        for wt_id, wt_list in self.entity_index.items():
            if wt_id != 'weather':
                continue
            for eid in wt_list:
                entity = self.entities[eid]
                speed_min, speed_max = entity.properties.get('speed', (0, 0))
                if speed_min <= wind_speed <= speed_max:
                    for rel in self.relations:
                        if rel.source == eid or rel.source == terrain:
                            inferences.append({
                                'weather': entity.name,
                                'hazard': entity.properties.get('hazard', 0),
                                'relation': rel.relation_type,
                                'weight': rel.weight,
                                'risk_score': entity.properties.get('hazard', 0) * rel.weight
                            })

        inferences.sort(key=lambda x: x['risk_score'], reverse=True)
        return inferences[:5]

    def recommend_route(self, weather_data: dict, terrain_type: str) -> dict:
        """基于知识图谱的智能推荐"""
        conditions = {'wind_speed': weather_data.get('wind_speed', 0), 'terrain': terrain_type}
        inferences = self.reason(conditions)
        total_risk = sum(inf['risk_score'] for inf in inferences) if inferences else 0

        recommendations = []
        if total_risk > 3:
            recommendations.append('建议推迟飞行或选择替代路线')
        if any(inf['relation'] == 'prohibits_flight' for inf in inferences):
            recommendations.append('当前气象条件禁止飞行')
        if any(inf['relation'] == 'requires_caution' for inf in inferences):
            recommendations.append('飞行需谨慎，建议降低高度')

        return {
            'total_risk': total_risk,
            'risk_level': 'HIGH' if total_risk > 3 else 'MEDIUM' if total_risk > 1 else 'LOW',
            'inferences': inferences,
            'recommendations': recommendations or ['气象条件良好，可以正常飞行'],
            'alternative_routes': self._find_alternative_routes(terrain_type, weather_data)
        }

    def _find_alternative_routes(self, terrain: str, weather: dict) -> List[str]:
        """寻找替代路线建议"""
        alternatives = []
        if terrain == 'mountain':
            alternatives.append('绕行山脊，选择平原走廊')
            alternatives.append('提升飞行高度至500m以上')
        elif weather.get('wind_speed', 0) > 8:
            alternatives.append('选择背风侧航线')
            alternatives.append('降低飞行速度至安全阈值')
        return alternatives
