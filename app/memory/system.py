from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import uuid
import math
from ..core.models import MemoryEntry, RuleMemory
from ..core.config import MemoryConfig


class VectorMemory:
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.entries: List[Dict[str, Any]] = []
        self._load_entries()
    
    def _load_entries(self):
        entries_path = Path(self.config.vector_db_path)
        if entries_path.exists():
            with open(entries_path, 'r', encoding='utf-8') as f:
                self.entries = json.load(f)
    
    def _save_entries(self):
        Path(self.config.vector_db_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.vector_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, indent=2, ensure_ascii=False, default=str)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def add(self, entry: MemoryEntry) -> str:
        entry_id = entry.id or str(uuid.uuid4())
        
        self.entries.append({
            'id': entry_id,
            'embedding': entry.embedding,
            'content': entry.content,
            'metadata': entry.metadata
        })
        
        self._save_entries()
        return entry_id
    
    async def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        scored_entries = []
        
        for entry in self.entries:
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if entry['metadata'].get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            similarity = self._cosine_similarity(query_embedding, entry['embedding'])
            scored_entries.append({
                'id': entry['id'],
                'content': entry['content'],
                'metadata': entry['metadata'],
                'distance': 1.0 - similarity,
                'similarity': similarity
            })
        
        scored_entries.sort(key=lambda x: x['similarity'], reverse=True)
        return scored_entries[:n_results]
    
    async def get_similar_decisions(
        self,
        query_embedding: List[float],
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        filter_metadata = None
        if file_type:
            filter_metadata = {'file_type': file_type}
        
        return await self.search(query_embedding, n_results=3, filter_metadata=filter_metadata)
    
    async def delete(self, entry_id: str) -> bool:
        original_count = len(self.entries)
        self.entries = [e for e in self.entries if e['id'] != entry_id]
        
        if len(self.entries) < original_count:
            self._save_entries()
            return True
        return False
    
    async def clear_all(self):
        self.entries = []
        self._save_entries()
    
    def count(self) -> int:
        return len(self.entries)


class RuleMemory:
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.rules: List[RuleMemory] = []
        self._load_rules()
    
    def _load_rules(self):
        rules_path = Path(self.config.rules_path)
        if rules_path.exists():
            with open(rules_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.rules = [RuleMemory(**rule) for rule in data]
    
    def _save_rules(self):
        Path(self.config.rules_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.rules_path, 'w', encoding='utf-8') as f:
            json.dump([rule.__dict__ for rule in self.rules], f, indent=2, ensure_ascii=False, default=str)
    
    def add_rule(self, pattern: str, action: str, target_folder: str, priority: int = 0) -> RuleMemory:
        rule = RuleMemory(
            pattern=pattern,
            action=action,
            target_folder=target_folder,
            priority=priority
        )
        self.rules.append(rule)
        self._save_rules()
        return rule
    
    def find_matching_rule(self, file_name: str, file_type: str) -> Optional[RuleMemory]:
        matching_rules = []
        
        for rule in self.rules:
            if rule.pattern.lower() in file_name.lower():
                matching_rules.append(rule)
            elif rule.pattern == file_type:
                matching_rules.append(rule)
        
        if matching_rules:
            matching_rules.sort(key=lambda r: (r.priority, -r.usage_count), reverse=True)
            return matching_rules[0]
        
        return None
    
    def update_rule_usage(self, rule: RuleMemory):
        rule.usage_count += 1
        rule.last_used = datetime.now()
        self._save_rules()
    
    def delete_rule(self, pattern: str) -> bool:
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.pattern != pattern]
        
        if len(self.rules) < original_count:
            self._save_rules()
            return True
        return False
    
    def get_all_rules(self) -> List[RuleMemory]:
        return self.rules.copy()


class MemorySystem:
    def __init__(self, config: Optional[MemoryConfig] = None):
        if config is None:
            from ..core.config import MemoryConfig
            config = MemoryConfig()
        self.vector_memory = VectorMemory(config)
        self.rule_memory = RuleMemory(config)
        self.config = config
    
    async def store_decision(
        self,
        file_path: str,
        target_folder: str,
        embedding: List[float],
        file_type: str,
        confidence: float,
        reasoning: str
    ) -> str:
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            embedding=embedding,
            content=f"File: {file_path} -> {target_folder}",
            metadata={
                'file_path': file_path,
                'target_folder': target_folder,
                'file_type': file_type,
                'confidence': confidence,
                'reasoning': reasoning,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return await self.vector_memory.add(entry)
    
    async def query_similar_decisions(
        self,
        embedding: List[float],
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return await self.vector_memory.get_similar_decisions(embedding, file_type)
    
    def find_rule(self, file_name: str, file_type: str) -> Optional[RuleMemory]:
        return self.rule_memory.find_matching_rule(file_name, file_type)
    
    def add_rule(self, pattern: str, action: str, target_folder: str, priority: int = 0) -> RuleMemory:
        return self.rule_memory.add_rule(pattern, action, target_folder, priority)
    
    def delete_rule(self, pattern: str) -> bool:
        return self.rule_memory.delete_rule(pattern)
    
    def get_all_rules(self) -> List[RuleMemory]:
        return self.rule_memory.get_all_rules()
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'vector_entries': self.vector_memory.count(),
            'rule_count': len(self.rule_memory.rules)
        }
