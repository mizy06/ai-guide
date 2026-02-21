from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from ..llm import TaskType, LLMRequest


class IntentType(Enum):
    FILE_ORGANIZATION = "file_organization"
    SEMANTIC_SEARCH = "semantic_search"
    MEMORY_LEARNING = "memory_learning"
    DEVELOPER_MODE = "developer_mode"
    CODE_MODIFICATION = "code_modification"
    DOCUMENT_UNDERSTANDING = "document_understanding"
    GENERAL_CHAT = "general_chat"


@dataclass
class Plan:
    intent: IntentType
    task_type: TaskType
    use_tool: bool
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    reasoning: str = ""
    confidence: float = 0.0
    requires_llm: bool = True


class Planner:
    SYSTEM_PROMPT = """You are the cognitive engine of an AI file intelligence system.

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
- General chat → chat

Tool Priority:
If a tool can solve the task, use the tool instead of LLM.

Available tools:
- move_file: Move files between directories
- search_files: Search for files by name or content
- read_file: Read file content safely
- generate_patch: Generate diff patches for code changes
- store_memory: Store decisions into memory

Confidence Rule:
If confidence < 0.8, ask user for confirmation.

Response Format:
INTENT: [intent_type]
TASK_TYPE: [task_type]
MODEL: [model_name]
REASON: [your reasoning]
ACTION: [tool_name or "call_llm"]
CONFIDENCE: [0.0-1.0]
"""

    def __init__(self):
        self._intent_patterns = {
            IntentType.FILE_ORGANIZATION: [
                r'organize|整理|分类|move|移动|文件'
            ],
            IntentType.SEMANTIC_SEARCH: [
                r'find|search|查找|搜索|find.*paper|搜索.*论文'
            ],
            IntentType.MEMORY_LEARNING: [
                r'learn|remember|记住|学习'
            ],
            IntentType.DEVELOPER_MODE: [
                r'developer|dev|开发|read code|读取代码'
            ],
            IntentType.CODE_MODIFICATION: [
                r'modify|change|edit|修改|代码|code'
            ],
            IntentType.DOCUMENT_UNDERSTANDING: [
                r'summarize|summary|总结|摘要|understand|理解'
            ],
            IntentType.GENERAL_CHAT: [
                r'hello|hi|what|how|why|help|帮助'
            ]
        }
        
        self._task_mapping = {
            IntentType.FILE_ORGANIZATION: TaskType.CLASSIFY,
            IntentType.SEMANTIC_SEARCH: TaskType.CLASSIFY,
            IntentType.MEMORY_LEARNING: TaskType.DECISION,
            IntentType.DEVELOPER_MODE: TaskType.CODEGEN,
            IntentType.CODE_MODIFICATION: TaskType.CODEGEN,
            IntentType.DOCUMENT_UNDERSTANDING: TaskType.SUMMARIZE,
            IntentType.GENERAL_CHAT: TaskType.CHAT
        }
    
    def analyze(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Plan:
        intent = self._detect_intent(user_input)
        task_type = self._task_mapping.get(intent, TaskType.CHAT)
        
        use_tool, tool_name, tool_args = self._decide_tool_usage(user_input, intent, context)
        
        reasoning = self._generate_reasoning(intent, task_type, use_tool, tool_name)
        confidence = self._calculate_confidence(intent, user_input, use_tool)
        
        return Plan(
            intent=intent,
            task_type=task_type,
            use_tool=use_tool,
            tool_name=tool_name,
            tool_args=tool_args,
            reasoning=reasoning,
            confidence=confidence,
            requires_llm=not use_tool
        )
    
    def _detect_intent(self, user_input: str) -> IntentType:
        user_input_lower = user_input.lower()
        
        for intent, patterns in self._intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    return intent
        
        return IntentType.GENERAL_CHAT
    
    def _decide_tool_usage(
        self,
        user_input: str,
        intent: IntentType,
        context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        if intent == IntentType.FILE_ORGANIZATION:
            if context and 'file_path' in context:
                return True, "move_file", {"source": context['file_path']}
        
        elif intent == IntentType.SEMANTIC_SEARCH:
            search_query = self._extract_search_query(user_input)
            if search_query:
                return True, "search_files", {"query": search_query}
        
        elif intent == IntentType.DEVELOPER_MODE:
            if context and 'file_path' in context:
                return True, "read_file", {"file_path": context['file_path']}
        
        elif intent == IntentType.CODE_MODIFICATION:
            if context and 'file_path' in context:
                return True, "generate_patch", {"file_path": context['file_path']}
        
        return False, None, None
    
    def _extract_search_query(self, user_input: str) -> Optional[str]:
        patterns = [
            r'find\s+(.+)',
            r'search\s+for\s+(.+)',
            r'查找\s*(.+)',
            r'搜索\s*(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _generate_reasoning(
        self,
        intent: IntentType,
        task_type: TaskType,
        use_tool: bool,
        tool_name: Optional[str]
    ) -> str:
        parts = []
        parts.append(f"Detected intent: {intent.value}")
        parts.append(f"Mapped to task type: {task_type.value}")
        
        if use_tool:
            parts.append(f"Using tool: {tool_name} (can solve directly)")
        else:
            parts.append("Using LLM (requires AI reasoning)")
        
        return " | ".join(parts)
    
    def _calculate_confidence(
        self,
        intent: IntentType,
        user_input: str,
        use_tool: bool
    ) -> float:
        base_confidence = 0.7
        
        if intent == IntentType.GENERAL_CHAT:
            base_confidence = 0.9
        
        if use_tool:
            base_confidence += 0.2
        
        if len(user_input) < 10:
            base_confidence -= 0.1
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def build_llm_request(
        self,
        plan: Plan,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMRequest:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
        
        if context:
            context_msg = f"\n\nContext: {context}"
            messages[-1]["content"] += context_msg
        
        return LLMRequest(
            messages=messages,
            task_type=plan.task_type,
            temperature=0.7,
            stream=False
        )
