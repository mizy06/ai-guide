import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from .models import ProviderType


@dataclass
class LLMProviderConfig:
    provider: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    timeout: int = 30
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EmbeddingConfig:
    model_name: str = "BAAI/bge-small-en-v1.5"
    device: str = "cpu"
    batch_size: int = 32
    dimension: int = 384


@dataclass
class MemoryConfig:
    vector_db_path: str = "data/chroma"
    collection_name: str = "file_memory"
    rules_path: str = "data/rules.json"
    max_memory_entries: int = 10000
    
    def __post_init__(self):
        Path(self.vector_db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.rules_path).parent.mkdir(parents=True, exist_ok=True)


@dataclass
class SafetyConfig:
    allowed_workspace: str = ""
    forbidden_patterns: list = field(default_factory=lambda: [
        "system32",
        "windows",
        "program files",
        ".git",
        "node_modules"
    ])
    require_confirmation_for_move: bool = True
    require_confirmation_for_delete: bool = True
    confidence_threshold: float = 0.7


@dataclass
class UIConfig:
    theme: str = "dark"
    accent_color: str = "#00d4ff"
    window_width: int = 1400
    window_height: int = 900
    log_max_lines: int = 1000


@dataclass
class Config:
    llm_providers: Dict[str, LLMProviderConfig] = field(default_factory=dict)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    active_provider: str = "openai"
    
    def __post_init__(self):
        if not self.llm_providers:
            self.llm_providers = {
                'openai': LLMProviderConfig(
                    provider=ProviderType.OPENAI,
                    model="gpt-4o-mini"
                ),
                'kimi': LLMProviderConfig(
                    provider=ProviderType.KIMI,
                    base_url="https://api.moonshot.cn/v1",
                    model="moonshot-v1-8k"
                ),
                'doubao': LLMProviderConfig(
                    provider=ProviderType.DOUBAO,
                    base_url="https://ark.cn-beijing.volces.com/api/v3",
                    model="doubao-pro-32k"
                ),
                'ollama': LLMProviderConfig(
                    provider=ProviderType.OLLAMA,
                    base_url="http://localhost:11434/v1",
                    model="llama3.2"
                )
            }
    
    @classmethod
    def load(cls, config_path: str = "config/config.json") -> 'Config':
        if not os.path.exists(config_path):
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)
            config = cls()
            config.save(config_path)
            return config
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = cls()
        
        if 'llm_providers' in data:
            config.llm_providers = {
                k: LLMProviderConfig(**v) for k, v in data['llm_providers'].items()
            }
        if 'embedding' in data:
            config.embedding = EmbeddingConfig(**data['embedding'])
        if 'memory' in data:
            config.memory = MemoryConfig(**data['memory'])
        if 'safety' in data:
            config.safety = SafetyConfig(**data['safety'])
        if 'ui' in data:
            config.ui = UIConfig(**data['ui'])
        if 'active_provider' in data:
            config.active_provider = data['active_provider']
        
        return config
    
    def save(self, config_path: str = "config/config.json") -> None:
        data = {
            'llm_providers': {
                k: v.to_dict() for k, v in self.llm_providers.items()
            },
            'embedding': asdict(self.embedding),
            'memory': asdict(self.memory),
            'safety': asdict(self.safety),
            'ui': asdict(self.ui),
            'active_provider': self.active_provider
        }
        
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_active_provider(self) -> LLMProviderConfig:
        return self.llm_providers.get(self.active_provider, self.llm_providers['openai'])
    
    def set_active_provider(self, provider_name: str) -> bool:
        if provider_name in self.llm_providers:
            self.active_provider = provider_name
            return True
        return False
