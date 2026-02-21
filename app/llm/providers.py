from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
import json
import time
from .base_provider import BaseLLMProvider, LLMResponse


class DeepSeekProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        super().__init__(api_key, "https://api.deepseek.com/v1", model)
    
    def _get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.00014, "output": 0.00028}
    
    async def _chat_completion_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def _chat_completion_non_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                usage=self._build_usage(prompt_tokens, completion_tokens),
                model=self.model,
                latency=latency
            )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None] | LLMResponse:
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        if stream:
            payload["stream"] = True
            return self._chat_completion_stream(headers, payload)
        else:
            return await self._chat_completion_non_stream(headers, payload, start_time)


class DoubaoProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "doubao-pro-32k"):
        super().__init__(api_key, "https://ark.cn-beijing.volces.com/api/v3", model)
    
    def _get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.0008, "output": 0.002}
    
    async def _chat_completion_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def _chat_completion_non_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                usage=self._build_usage(prompt_tokens, completion_tokens),
                model=self.model,
                latency=latency
            )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None] | LLMResponse:
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        if stream:
            payload["stream"] = True
            return self._chat_completion_stream(headers, payload)
        else:
            return await self._chat_completion_non_stream(headers, payload, start_time)


class TongyiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        super().__init__(api_key, "https://dashscope.aliyuncs.com/compatible-mode/v1", model)
    
    def _get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.0008, "output": 0.002}
    
    async def _chat_completion_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def _chat_completion_non_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                usage=self._build_usage(prompt_tokens, completion_tokens),
                model=self.model,
                latency=latency
            )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None] | LLMResponse:
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        if stream:
            payload["stream"] = True
            return self._chat_completion_stream(headers, payload)
        else:
            return await self._chat_completion_non_stream(headers, payload, start_time)


class ZhipuProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "glm-4"):
        super().__init__(api_key, "https://open.bigmodel.cn/api/paas/v4", model)
    
    def _get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.001, "output": 0.002}
    
    async def _chat_completion_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def _chat_completion_non_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                usage=self._build_usage(prompt_tokens, completion_tokens),
                model=self.model,
                latency=latency
            )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None] | LLMResponse:
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        if stream:
            payload["stream"] = True
            return self._chat_completion_stream(headers, payload)
        else:
            return await self._chat_completion_non_stream(headers, payload, start_time)


class BaichuanProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "Baichuan4"):
        super().__init__(api_key, "https://api.baichuan-ai.com/v1", model)
    
    def _get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.001, "output": 0.002}
    
    async def _chat_completion_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def _chat_completion_non_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                usage=self._build_usage(prompt_tokens, completion_tokens),
                model=self.model,
                latency=latency
            )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None] | LLMResponse:
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        if stream:
            payload["stream"] = True
            return self._chat_completion_stream(headers, payload)
        else:
            return await self._chat_completion_non_stream(headers, payload, start_time)


class WenxinProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "ERNIE-Bot-4"):
        super().__init__(api_key, "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat", model)
    
    def _get_cost_per_1k_tokens(self) -> Dict[str, float]:
        return {"input": 0.0012, "output": 0.0012}
    
    async def _chat_completion_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def _chat_completion_non_stream(
        self,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            latency = time.time() - start_time
            
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                usage=self._build_usage(prompt_tokens, completion_tokens),
                model=self.model,
                latency=latency
            )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None] | LLMResponse:
        start_time = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        if stream:
            payload["stream"] = True
            return self._chat_completion_stream(headers, payload)
        else:
            return await self._chat_completion_non_stream(headers, payload, start_time)
