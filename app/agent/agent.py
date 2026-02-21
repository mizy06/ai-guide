from typing import Dict, Any, Optional, AsyncGenerator
import logging

from ..llm import LLMRouter, TaskType
from ..memory import MemorySystem
from ..tools import ToolRegistry
from ..core.models import FileMetadata
from .planner import Planner, Plan
from .executor import Executor
from .memory_reader import MemoryReader


class FileIntelligenceAgent:
    SYSTEM_PROMPT = """You are cognitive engine of an AI file intelligence system.

You never call any LLM directly. You must go through the LLM router.

Your workflow:
1. Understand user intent
2. Map intent to task type
3. Decide: use tool OR call LLM

Task Mapping:
- File classification → classify
- Complex reasoning → decision
- Code modification → codegen
- Document understanding → summarize

Tool Priority:
If a tool can solve the task, use the tool instead of LLM.

Memory Usage:
Before making a decision:
- Query user habit memory
- Reuse past confirmed actions

Confidence Rule:
If confidence < 0.8:
- Ask user for confirmation.

Response Format:
INTENT: [intent_type]
TASK_TYPE: [task_type]
MODEL: [model_name]
REASON: [your reasoning]
ACTION: [action to take or question to ask]
CONFIDENCE: [0.0-1.0]
"""

    def __init__(
        self,
        llm_router: LLMRouter,
        memory_system: MemorySystem,
        tool_registry: ToolRegistry
    ):
        self.llm_router = llm_router
        self.memory_system = memory_system
        self.tool_registry = tool_registry
        
        self.planner = Planner()
        self.executor = Executor(llm_router, tool_registry)
        self.memory_reader = MemoryReader(memory_system)
        
        self.current_file: Optional[FileMetadata] = None
        self.developer_mode = False
        
        self.logger = logging.getLogger(__name__)
    
    async def process_file(self, file_path: str) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"type": "status", "message": "Extracting file metadata..."}
        
        file_metadata = await self._extract_file_metadata(file_path)
        self.current_file = file_metadata
        
        yield {"type": "status", "message": "Reading memory context..."}
        
        memory_context = await self.memory_reader.read_context(file_metadata)
        
        yield {"type": "status", "message": "Planning action..."}
        
        plan = self.planner.analyze(
            f"Organize file: {file_metadata.name}",
            context={"file_metadata": file_metadata, "memory": memory_context}
        )
        
        plan.confidence = min(plan.confidence + memory_context.confidence_boost, 1.0)
        
        yield {
            "type": "plan",
            "intent": plan.intent.value,
            "task_type": plan.task_type.value,
            "reasoning": plan.reasoning,
            "confidence": plan.confidence
        }
        
        if plan.confidence < 0.8:
            yield {
                "type": "confirmation_required",
                "message": f"Low confidence ({plan.confidence:.0%}). Please confirm.",
                "plan": plan
            }
        else:
            async for result in self.executor.execute(
                plan,
                f"Organize file: {file_metadata.name}",
                context={"file_path": file_path, "memory": memory_context}
            ):
                yield result
    
    async def process_chat(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"type": "status", "message": "Analyzing request..."}
        
        plan = self.planner.analyze(message)
        
        yield {
            "type": "plan",
            "intent": plan.intent.value,
            "task_type": plan.task_type.value,
            "reasoning": plan.reasoning,
            "confidence": plan.confidence
        }
        
        async for result in self.executor.execute(plan, message):
            yield result
    
    async def process_developer_task(
        self,
        task: str,
        file_path: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        self.developer_mode = True
        
        context = {}
        if file_path:
            context["file_path"] = file_path
        
        plan = self.planner.analyze(task, context)
        
        yield {
            "type": "plan",
            "intent": plan.intent.value,
            "task_type": plan.task_type.value,
            "reasoning": plan.reasoning,
            "confidence": plan.confidence
        }
        
        async for result in self.executor.execute(plan, task, context):
            yield result
    
    async def confirm_decision(
        self,
        file_path: str,
        target_folder: str,
        confidence: float,
        reasoning: str
    ) -> Dict[str, Any]:
        if not self.current_file:
            return {"success": False, "error": "No current file"}
        
        result = await self.tool_registry.execute_tool(
            "move_file",
            source=file_path,
            destination=target_folder
        )
        
        if result.success:
            await self.memory_reader.store_decision(
                file_path,
                target_folder,
                self.current_file.embedding or [],
                self.current_file.extension,
                confidence,
                reasoning
            )
        
        return {"success": result.success, "error": result.error}
    
    async def _extract_file_metadata(self, file_path: str) -> FileMetadata:
        from pathlib import Path
        from datetime import datetime
        import mimetypes
        
        path = Path(file_path)
        stat = path.stat()
        
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"
        
        content_preview = ""
        extracted_text = None
        
        if path.stat().st_size < 1024 * 1024:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content_preview = f.read(500)
                    extracted_text = content_preview
            except Exception:
                pass
        
        return FileMetadata(
            path=str(path),
            name=path.name,
            size=stat.st_size,
            extension=path.suffix.lower(),
            mime_type=mime_type,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            content_preview=content_preview,
            extracted_text=extracted_text
        )
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "developer_mode": self.developer_mode,
            "current_file": self.current_file.path if self.current_file else None,
            "memory_stats": self.memory_reader.get_memory_stats()
        }
