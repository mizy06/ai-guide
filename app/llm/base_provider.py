from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import time


class TaskType(Enum):
    CLASSIFY = "classify"
    DECISION = "decision"
    SUMMARIZE = "summarize"
    CODEGEN = "codegen"
    CHAT = "chat"


@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, Any]
    model: str
    latency: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "usage": self.usage,
            "model": self.model,
            "latency": self.latency
        }


@dataclass
class LLMRequest:
    messages: List[Dict[str, str]]
    task_type: TaskType
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None


class BaseLLMProvider(ABC):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._cost_per_1k_tokens = self._get_cost_per_1k_tokens()
    
    @abstractmethod
    def _get_cost_per_1k_tokens(self) -> Dict[str, float]:
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None] | LLMResponse:
        pass
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        input_cost = (prompt_tokens / 1000) * self._cost_per_1k_tokens.get("input", 0.001)
        output_cost = (completion_tokens / 1000) * self._cost_per_1k_tokens.get("output", 0.002)
        return input_cost + output_cost
    
    def _build_usage(self, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": self._calculate_cost(prompt_tokens, completion_tokens)
        }
