from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from ..memory import MemorySystem
from ..core.models import FileMetadata


@dataclass
class MemoryContext:
    similar_decisions: List[Dict[str, Any]]
    user_rules: List[Dict[str, Any]]
    confidence_boost: float = 0.0
    reasoning: str = ""


class MemoryReader:
    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system
        self.logger = logging.getLogger(__name__)
    
    async def read_context(
        self,
        file_metadata: Optional[FileMetadata] = None,
        query_embedding: Optional[List[float]] = None,
        file_type: Optional[str] = None
    ) -> MemoryContext:
        similar_decisions = []
        user_rules = []
        
        if file_metadata and file_metadata.embedding:
            similar_decisions = await self.memory_system.query_similar_decisions(
                file_metadata.embedding,
                file_metadata.extension
            )
        
        if file_type:
            rule = self.memory_system.find_rule(file_metadata.name if file_metadata else "", file_type)
            if rule:
                user_rules.append({
                    "pattern": rule.pattern,
                    "action": rule.action,
                    "target_folder": rule.target_folder,
                    "usage_count": rule.usage_count
                })
        
        confidence_boost = self._calculate_confidence_boost(similar_decisions, user_rules)
        reasoning = self._generate_reasoning(similar_decisions, user_rules)
        
        return MemoryContext(
            similar_decisions=similar_decisions,
            user_rules=user_rules,
            confidence_boost=confidence_boost,
            reasoning=reasoning
        )
    
    def _calculate_confidence_boost(
        self,
        similar_decisions: List[Dict[str, Any]],
        user_rules: List[Dict[str, Any]]
    ) -> float:
        boost = 0.0
        
        if similar_decisions:
            avg_confidence = sum(
                d.get('metadata', {}).get('confidence', 0.5)
                for d in similar_decisions
            ) / len(similar_decisions)
            boost += avg_confidence * 0.3
        
        if user_rules:
            total_usage = sum(r.get('usage_count', 0) for r in user_rules)
            boost += min(total_usage * 0.05, 0.2)
        
        return min(boost, 0.5)
    
    def _generate_reasoning(
        self,
        similar_decisions: List[Dict[str, Any]],
        user_rules: List[Dict[str, Any]]
    ) -> str:
        parts = []
        
        if similar_decisions:
            parts.append(f"Found {len(similar_decisions)} similar past decisions")
            for decision in similar_decisions[:2]:
                metadata = decision.get('metadata', {})
                parts.append(
                    f"  - {metadata.get('file_path', 'unknown')} → "
                    f"{metadata.get('target_folder', 'unknown')} "
                    f"(confidence: {metadata.get('confidence', 0):.2f})"
                )
        
        if user_rules:
            parts.append(f"Found {len(user_rules)} matching rules")
            for rule in user_rules:
                parts.append(
                    f"  - Rule: {rule['pattern']} → {rule['target_folder']} "
                    f"(used {rule['usage_count']} times)"
                )
        
        if not parts:
            parts.append("No relevant memory found")
        
        return "\n".join(parts)
    
    async def store_decision(
        self,
        file_path: str,
        target_folder: str,
        embedding: List[float],
        file_type: str,
        confidence: float,
        reasoning: str
    ) -> str:
        return await self.memory_system.store_decision(
            file_path,
            target_folder,
            embedding,
            file_type,
            confidence,
            reasoning
        )
    
    def get_memory_stats(self) -> Dict[str, Any]:
        return self.memory_system.get_stats()
