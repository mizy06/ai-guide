from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio


class EventType(Enum):
    FILE_DROPPED = "file_dropped"
    FILE_PROCESSED = "file_processed"
    MEMORY_UPDATED = "memory_updated"
    AGENT_THINKING = "agent_thinking"
    AGENT_DECISION = "agent_decision"
    MODE_CHANGED = "mode_changed"
    PROVIDER_CHANGED = "provider_changed"
    ERROR_OCCURRED = "error_occurred"
    TOOL_EXECUTED = "tool_executed"


@dataclass
class Event:
    type: EventType
    data: Any = None
    timestamp: float = 0
    source: str = ""
    
    def __post_init__(self):
        import time
        if self.timestamp == 0:
            self.timestamp = time.time()


class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, event_type: EventType, callback: Callable) -> None:
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    
    def subscribe_sync(self, event_type: EventType, callback: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    async def publish(self, event: Event) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(event.type, []).copy()
        
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                error_event = Event(
                    type=EventType.ERROR_OCCURRED,
                    data={'error': str(e), 'event': event.type.value}
                )
                await self.publish(error_event)
    
    async def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        async with self._lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
