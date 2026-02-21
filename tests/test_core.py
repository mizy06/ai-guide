import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core import Config, FileMetadata, EventBus, Event, EventType
from app.llm import LLMRouter
from app.memory import MemorySystem
from app.tools import ToolRegistry
from app.agent import FileIntelligenceAgent


def test_config_load():
    config = Config.load("config/config.json")
    assert config is not None
    assert "openai" in config.llm_providers
    assert config.active_provider == "openai"


def test_file_metadata():
    from datetime import datetime
    
    metadata = FileMetadata(
        path="test.txt",
        name="test.txt",
        size=1024,
        extension=".txt",
        mime_type="text/plain",
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    assert metadata.name == "test.txt"
    assert metadata.size == 1024


def test_event_bus():
    import asyncio
    
    async def test():
        bus = EventBus()
        received = []
        
        async def handler(event):
            received.append(event)
        
        await bus.subscribe(EventType.FILE_DROPPED, handler)
        
        event = Event(type=EventType.FILE_DROPPED, data={"file": "test.txt"})
        await bus.publish(event)
        
        assert len(received) == 1
        assert received[0].data["file"] == "test.txt"
    
    asyncio.run(test())


def test_tool_registry():
    from app.core import SafetyConfig
    
    safety = SafetyConfig(allowed_workspace=".")
    registry = ToolRegistry(safety)
    
    tools = registry.get_all_tools()
    assert len(tools) > 0
    
    assert "move_file" in [t["name"] for t in tools]
    assert "search_files" in [t["name"] for t in tools]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
