from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import logging

from ..llm import LLMRouter, LLMRequest, TaskType
from ..tools import ToolRegistry, ToolResult
from .planner import Plan, IntentType


class Executor:
    def __init__(
        self,
        llm_router: LLMRouter,
        tool_registry: ToolRegistry
    ):
        self.llm_router = llm_router
        self.tool_registry = tool_registry
        self.logger = logging.getLogger(__name__)
    
    async def execute(
        self,
        plan: Plan,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"type": "status", "message": f"Executing plan: {plan.intent.value}"}
        
        if plan.use_tool and plan.tool_name:
            yield await self._execute_tool(plan, user_input, context)
        elif plan.requires_llm:
            async for result in self._execute_llm(plan, user_input, context):
                yield result
        
        yield {"type": "complete", "confidence": plan.confidence}
    
    async def _execute_tool(
        self,
        plan: Plan,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        yield {"type": "status", "message": f"Executing tool: {plan.tool_name}"}
        
        try:
            tool_args = plan.tool_args or {}
            
            if context:
                tool_args.update(context)
            
            result = await self.tool_registry.execute_tool(
                plan.tool_name,
                **tool_args
            )
            
            if result.success:
                yield {
                    "type": "tool_result",
                    "tool": plan.tool_name,
                    "result": result.data,
                    "confidence": result.confidence
                }
                
                if result.requires_confirmation:
                    yield {
                        "type": "confirmation_required",
                        "message": "This action requires your confirmation",
                        "result": result
                    }
            else:
                yield {
                    "type": "error",
                    "message": f"Tool execution failed: {result.error}"
                }
        
        except Exception as e:
            self.logger.error(f"Tool execution error: {e}")
            yield {
                "type": "error",
                "message": f"Error executing tool: {str(e)}"
            }
    
    async def _execute_llm(
        self,
        plan: Plan,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"type": "status", "message": f"Calling LLM for task: {plan.task_type.value}"}
        
        try:
            messages = [
                {"role": "system", "content": self._get_system_prompt(plan.intent)},
                {"role": "user", "content": user_input}
            ]
            
            if context:
                context_str = self._format_context(context)
                messages[-1]["content"] += f"\n\nContext:\n{context_str}"
            
            request = LLMRequest(
                messages=messages,
                task_type=plan.task_type,
                temperature=0.7,
                stream=True
            )
            
            response_stream = await self.llm_router.route(request)
            
            content = ""
            if hasattr(response_stream, '__aiter__'):
                async for chunk in response_stream:
                    content += chunk
                    yield {
                        "type": "llm_chunk",
                        "content": chunk,
                        "task_type": plan.task_type.value
                    }
            else:
                content = response_stream.content
                yield {
                    "type": "llm_response",
                    "content": content,
                    "task_type": plan.task_type.value,
                    "usage": response_stream.usage,
                    "model": response_stream.model,
                    "latency": response_stream.latency
                }
        
        except Exception as e:
            self.logger.error(f"LLM execution error: {e}")
            yield {
                "type": "error",
                "message": f"Error calling LLM: {str(e)}"
            }
    
    def _get_system_prompt(self, intent: IntentType) -> str:
        prompts = {
            IntentType.FILE_ORGANIZATION: """You are a file organization expert. Analyze files and suggest appropriate folders for organization.""",
            IntentType.SEMANTIC_SEARCH: """You are a search expert. Help users find files based on semantic queries.""",
            IntentType.MEMORY_LEARNING: """You are a learning system. Remember user preferences and decisions.""",
            IntentType.DEVELOPER_MODE: """You are a code analysis expert. Read and understand code, propose changes via patches only.""",
            IntentType.CODE_MODIFICATION: """You are a code modification expert. Generate patches for code changes, never overwrite directly.""",
            IntentType.DOCUMENT_UNDERSTANDING: """You are a document analysis expert. Summarize and understand document contents.""",
            IntentType.GENERAL_CHAT: """You are a helpful AI assistant. Respond to user queries helpfully and concisely."""
        }
        return prompts.get(intent, prompts[IntentType.GENERAL_CHAT])
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        lines = []
        for key, value in context.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
