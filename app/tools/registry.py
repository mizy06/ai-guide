from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
from pathlib import Path
import shutil
import os
from ..core.models import ToolResult, FileMetadata, FileDecision
from ..core.config import SafetyConfig


class BaseTool(ABC):
    def __init__(self, name: str, description: str, safety_config: SafetyConfig):
        self.name = name
        self.description = description
        self.safety_config = safety_config
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
    
    def _check_safety(self, path: str) -> bool:
        workspace = Path(self.safety_config.allowed_workspace).resolve()
        target_path = Path(path).resolve()
        
        try:
            target_path.relative_to(workspace)
            return True
        except ValueError:
            for pattern in self.safety_config.forbidden_patterns:
                if pattern.lower() in target_path.parts:
                    return False
            return False


class MoveFileTool(BaseTool):
    def __init__(self, safety_config: SafetyConfig):
        super().__init__(
            name="move_file",
            description="Move a file from source to destination folder",
            safety_config=safety_config
        )
    
    async def execute(self, source: str, destination: str, **kwargs) -> ToolResult:
        if not self._check_safety(source) or not self._check_safety(destination):
            return ToolResult(
                success=False,
                error="Path outside allowed workspace or forbidden directory"
            )
        
        try:
            src_path = Path(source)
            dst_path = Path(destination)
            
            if not src_path.exists():
                return ToolResult(success=False, error=f"Source file not found: {source}")
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            return ToolResult(
                success=True,
                data={"source": source, "destination": str(dst_path)},
                confidence=1.0
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SearchFilesTool(BaseTool):
    def __init__(self, safety_config: SafetyConfig):
        super().__init__(
            name="search_files",
            description="Search for files by name or content pattern",
            safety_config=safety_config
        )
    
    async def execute(
        self,
        query: str,
        search_path: Optional[str] = None,
        file_type: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            base_path = Path(search_path or self.safety_config.allowed_workspace)
            
            if not self._check_safety(str(base_path)):
                return ToolResult(
                    success=False,
                    error="Search path outside allowed workspace"
                )
            
            results = []
            
            for root, dirs, files in os.walk(base_path):
                dirs[:] = [d for d in dirs if not any(p in d.lower() for p in self.safety_config.forbidden_patterns)]
                
                for file in files:
                    file_path = Path(root) / file
                    
                    if file_type and not file.lower().endswith(file_type.lower()):
                        continue
                    
                    if query.lower() in file.lower():
                        results.append({
                            "path": str(file_path),
                            "name": file,
                            "size": file_path.stat().st_size
                        })
            
            return ToolResult(
                success=True,
                data={"results": results, "count": len(results)},
                confidence=1.0
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadFileTool(BaseTool):
    def __init__(self, safety_config: SafetyConfig):
        super().__init__(
            name="read_file",
            description="Read file content safely",
            safety_config=safety_config
        )
    
    async def execute(self, file_path: str, max_lines: int = 100, **kwargs) -> ToolResult:
        if not self._check_safety(file_path):
            return ToolResult(
                success=False,
                error="File path outside allowed workspace"
            )
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                return ToolResult(success=False, error=f"File not found: {file_path}")
            
            if path.stat().st_size > 10 * 1024 * 1024:
                return ToolResult(
                    success=False,
                    error="File too large (>10MB)"
                )
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip('\n'))
            
            return ToolResult(
                success=True,
                data={
                    "content": '\n'.join(lines),
                    "lines_read": len(lines),
                    "total_lines": sum(1 for _ in open(path, 'r', encoding='utf-8', errors='ignore'))
                },
                confidence=1.0
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GeneratePatchTool(BaseTool):
    def __init__(self, safety_config: SafetyConfig):
        super().__init__(
            name="generate_patch",
            description="Generate a diff patch for code changes (developer mode only)",
            safety_config=safety_config
        )
    
    async def execute(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
        **kwargs
    ) -> ToolResult:
        if not self._check_safety(file_path):
            return ToolResult(
                success=False,
                error="File path outside allowed workspace"
            )
        
        try:
            import difflib
            
            diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                lineterm=''
            )
            
            patch_content = ''.join(diff)
            
            return ToolResult(
                success=True,
                data={
                    "patch": patch_content,
                    "file_path": file_path,
                    "changes_added": new_content.count('\n') - old_content.count('\n')
                },
                confidence=1.0,
                requires_confirmation=True
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class StoreMemoryTool(BaseTool):
    def __init__(self, safety_config: SafetyConfig):
        super().__init__(
            name="store_memory",
            description="Store a decision or preference into memory",
            safety_config=safety_config
        )
    
    async def execute(
        self,
        content: str,
        metadata: Dict[str, Any],
        **kwargs
    ) -> ToolResult:
        try:
            return ToolResult(
                success=True,
                data={
                    "stored": True,
                    "content": content,
                    "metadata": metadata
                },
                confidence=1.0
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ToolRegistry:
    def __init__(self, safety_config: SafetyConfig):
        self.safety_config = safety_config
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.register_tool(MoveFileTool(self.safety_config))
        self.register_tool(SearchFilesTool(self.safety_config))
        self.register_tool(ReadFileTool(self.safety_config))
        self.register_tool(GeneratePatchTool(self.safety_config))
        self.register_tool(StoreMemoryTool(self.safety_config))
    
    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[Dict[str, str]]:
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools.values()
        ]
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
            for tool in self.tools.values()
        ]
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {name}")
        
        return await tool.execute(**kwargs)
