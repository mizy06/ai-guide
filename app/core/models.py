from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import hashlib
import os


class TaskType(Enum):
    FILE_ORGANIZATION = "file_organization"
    SEMANTIC_SEARCH = "semantic_search"
    MEMORY_LEARNING = "memory_learning"
    DEVELOPER_MODE = "developer_mode"


class ProviderType(Enum):
    OPENAI = "openai"
    KIMI = "kimi"
    DOUBAO = "doubao"
    OLLAMA = "ollama"


@dataclass
class FileMetadata:
    path: str
    name: str
    size: int
    extension: str
    mime_type: str
    created_at: datetime
    modified_at: datetime
    content_preview: Optional[str] = None
    content_hash: Optional[str] = None
    extracted_text: Optional[str] = None
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if self.content_hash is None and os.path.exists(self.path):
            self.content_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        hasher = hashlib.sha256()
        try:
            with open(self.path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return hashlib.sha256(self.path.encode()).hexdigest()


@dataclass
class FileDecision:
    file_path: str
    target_folder: str
    confidence: float
    reasoning: str
    suggested_by: str
    user_confirmed: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MemoryEntry:
    id: str
    embedding: List[float]
    content: str
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'embedding': self.embedding,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class RuleMemory:
    pattern: str
    action: str
    target_folder: str
    priority: int = 0
    usage_count: int = 0
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentState:
    current_task: Optional[TaskType] = None
    current_file: Optional[FileMetadata] = None
    thinking: bool = False
    confidence: float = 0.0
    provider: ProviderType = ProviderType.OPENAI
    developer_mode: bool = False
    allowed_workspace: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_task': self.current_task.value if self.current_task else None,
            'current_file': self.current_file.path if self.current_file else None,
            'thinking': self.thinking,
            'confidence': self.confidence,
            'provider': self.provider.value,
            'developer_mode': self.developer_mode,
            'allowed_workspace': self.allowed_workspace
        }


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    confidence: float = 0.0
    requires_confirmation: bool = False
