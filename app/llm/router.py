from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
from pathlib import Path
import yaml

from .base_provider import BaseLLMProvider, LLMResponse, TaskType, LLMRequest
from .providers import (
    DeepSeekProvider, DoubaoProvider, TongyiProvider,
    ZhipuProvider, BaichuanProvider, WenxinProvider
)


@dataclass
class RequestLog:
    timestamp: datetime
    task_type: TaskType
    provider: str
    model: str
    latency: float
    tokens: int
    cost: float
    success: bool
    error: Optional[str] = None


@dataclass
class RouterStats:
    total_requests: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    avg_latency: float = 0.0
    success_rate: float = 1.0
    provider_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class LLMRouter:
    def __init__(self, config_path: str = "config/models.yaml"):
        self.config_path = config_path
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.task_routing: Dict[TaskType, str] = {}
        self.logs: List[RequestLog] = []
        self.stats = RouterStats()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self._load_config()
        self._initialize_providers()
    
    def _load_config(self):
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._get_default_config()
            self._save_config()
        
        self._setup_task_routing()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "models": {
                "classify": "doubao",
                "decision": "deepseek",
                "summarize": "tongyi",
                "codegen": "deepseek",
                "chat": "doubao"
            },
            "api_keys": {
                "deepseek": "",
                "doubao": "",
                "tongyi": "",
                "zhipu": "",
                "baichuan": "",
                "wenxin": ""
            },
            "model_settings": {
                "deepseek": {"model": "deepseek-chat"},
                "doubao": {"model": "doubao-pro-32k"},
                "tongyi": {"model": "qwen-turbo"},
                "zhipu": {"model": "glm-4"},
                "baichuan": {"model": "Baichuan4"},
                "wenxin": {"model": "ERNIE-Bot-4"}
            },
            "fallback": {
                "enabled": True,
                "max_retries": 3,
                "retry_delay": 1.0
            }
        }
    
    def _save_config(self):
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
    
    def _setup_task_routing(self):
        models_config = self.config.get("models", {})
        for task_name, provider_name in models_config.items():
            try:
                task_type = TaskType(task_name)
                self.task_routing[task_type] = provider_name
            except ValueError:
                self.logger.warning(f"Unknown task type: {task_name}")
    
    def _initialize_providers(self):
        provider_classes = {
            "deepseek": DeepSeekProvider,
            "doubao": DoubaoProvider,
            "tongyi": TongyiProvider,
            "zhipu": ZhipuProvider,
            "baichuan": BaichuanProvider,
            "wenxin": WenxinProvider
        }
        
        api_keys = self.config.get("api_keys", {})
        model_settings = self.config.get("model_settings", {})
        
        for provider_name, api_key in api_keys.items():
            if api_key and provider_name in provider_classes:
                settings = model_settings.get(provider_name, {})
                model = settings.get("model", provider_classes[provider_name].__name__.replace("Provider", "").lower())
                
                try:
                    provider = provider_classes[provider_name](api_key, model)
                    self.providers[provider_name] = provider
                    self.logger.info(f"Initialized provider: {provider_name}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize {provider_name}: {e}")
    
    def get_available_providers(self) -> List[str]:
        return list(self.providers.keys())
    
    def get_task_routing(self) -> Dict[str, str]:
        return {task.value: provider for task, provider in self.task_routing.items()}
    
    def update_task_routing(self, task_type: TaskType, provider_name: str) -> bool:
        if provider_name not in self.providers:
            self.logger.error(f"Provider not available: {provider_name}")
            return False
        
        self.task_routing[task_type] = provider_name
        self.config["models"][task_type.value] = provider_name
        self._save_config()
        return True
    
    async def route(
        self,
        request: LLMRequest,
        preferred_provider: Optional[str] = None
    ) -> AsyncGenerator[str, None] | LLMResponse:
        provider_name = preferred_provider or self.task_routing.get(request.task_type)
        
        if not provider_name:
            provider_name = list(self.providers.keys())[0] if self.providers else None
        
        if not provider_name:
            raise RuntimeError("No available providers")
        
        if provider_name not in self.providers:
            available = list(self.providers.keys())
            if available:
                provider_name = available[0]
                self.logger.warning(f"Requested provider not available, using: {provider_name}")
            else:
                raise RuntimeError(f"Provider {provider_name} not available and no fallback")
        
        return await self._execute_with_retry(provider_name, request)
    
    async def _execute_with_retry(
        self,
        provider_name: str,
        request: LLMRequest
    ) -> AsyncGenerator[str, None] | LLMResponse:
        fallback_config = self.config.get("fallback", {})
        max_retries = fallback_config.get("max_retries", 3)
        retry_delay = fallback_config.get("retry_delay", 1.0)
        enabled = fallback_config.get("enabled", True)
        
        providers_to_try = [provider_name]
        if enabled:
            providers_to_try.extend([p for p in self.providers.keys() if p != provider_name])
        
        last_error = None
        
        for attempt, current_provider in enumerate(providers_to_try[:max_retries]):
            try:
                provider = self.providers[current_provider]
                
                if request.stream:
                    return await provider.chat_completion(
                        request.messages,
                        request.temperature,
                        request.max_tokens,
                        True,
                        request.tools
                    )
                else:
                    start_time = asyncio.get_event_loop().time()
                    response = await provider.chat_completion(
                        request.messages,
                        request.temperature,
                        request.max_tokens,
                        False,
                        request.tools
                    )
                    
                    self._log_request(
                        request.task_type,
                        current_provider,
                        response.model,
                        response.latency,
                        response.usage["total_tokens"],
                        response.usage["cost"],
                        True
                    )
                    
                    return response
                    
            except Exception as e:
                last_error = e
                self.logger.error(f"Provider {current_provider} failed: {e}")
                
                self._log_request(
                    request.task_type,
                    current_provider,
                    "",
                    0,
                    0,
                    0,
                    False,
                    str(e)
                )
                
                if attempt < len(providers_to_try[:max_retries]) - 1:
                    await asyncio.sleep(retry_delay)
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    def _log_request(
        self,
        task_type: TaskType,
        provider: str,
        model: str,
        latency: float,
        tokens: int,
        cost: float,
        success: bool,
        error: Optional[str] = None
    ):
        log = RequestLog(
            timestamp=datetime.now(),
            task_type=task_type,
            provider=provider,
            model=model,
            latency=latency,
            tokens=tokens,
            cost=cost,
            success=success,
            error=error
        )
        
        self.logs.append(log)
        
        self.stats.total_requests += 1
        if success:
            self.stats.total_cost += cost
            self.stats.total_tokens += tokens
            self.stats.avg_latency = (
                (self.stats.avg_latency * (self.stats.total_requests - 1) + latency) / 
                self.stats.total_requests
            )
        
        success_count = sum(1 for log in self.logs if log.success)
        self.stats.success_rate = success_count / len(self.logs) if self.logs else 1.0
        
        if provider not in self.stats.provider_stats:
            self.stats.provider_stats[provider] = {
                "requests": 0,
                "cost": 0.0,
                "tokens": 0,
                "errors": 0
            }
        
        self.stats.provider_stats[provider]["requests"] += 1
        if success:
            self.stats.provider_stats[provider]["cost"] += cost
            self.stats.provider_stats[provider]["tokens"] += tokens
        else:
            self.stats.provider_stats[provider]["errors"] += 1
    
    def get_stats(self) -> RouterStats:
        return self.stats
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        recent_logs = self.logs[-limit:]
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "task_type": log.task_type.value,
                "provider": log.provider,
                "model": log.model,
                "latency": log.latency,
                "tokens": log.tokens,
                "cost": log.cost,
                "success": log.success,
                "error": log.error
            }
            for log in recent_logs
        ]
    
    def clear_logs(self):
        self.logs.clear()
        self.stats = RouterStats()
