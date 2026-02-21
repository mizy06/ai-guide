from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QThread
import sys
import asyncio
from pathlib import Path

from .core import EventBus, Event, EventType, SafetyConfig
from .llm import LLMRouter
from .memory import MemorySystem
from .tools import ToolRegistry
from .agent import FileIntelligenceAgent
from .gui import MainWindow


class AsyncWorker(QThread):
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, async_gen):
        super().__init__()
        self.async_gen = async_gen
        self.loop = None
    
    def run(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            async def run_gen():
                try:
                    async for _ in self.async_gen:
                        pass
                except Exception as e:
                    self.error.emit(str(e))
            
            self.loop.run_until_complete(run_gen())
        except Exception as e:
            self.error.emit(str(e))
        finally:
            try:
                if self.loop and not self.loop.is_closed():
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    self.loop.close()
            except Exception:
                pass
            self.finished.emit()


class Application(QObject):
    def __init__(self):
        super().__init__()
        self.app = None
        self.main_window = None
        self.event_bus = None
        self.llm_router = None
        self.memory_system = None
        self.tool_registry = None
        self.agent = None
        self.loop = None
    
    def initialize(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        self.event_bus = EventBus()
        self.llm_router = LLMRouter()
        self.memory_system = MemorySystem()
        self.tool_registry = ToolRegistry(SafetyConfig())
        self.agent = FileIntelligenceAgent(
            self.llm_router,
            self.memory_system,
            self.tool_registry
        )
        
        self.main_window = MainWindow()
        self._connect_signals()
        self._setup_workspace()
        self._update_control_panel()
        
        return self.app
    
    def _connect_signals(self):
        top_bar = self.main_window.get_top_bar()
        center_panel = self.main_window.get_center_panel()
        right_panel = self.main_window.get_right_panel()
        left_panel = self.main_window.get_left_panel()
        control_panel = self.main_window.get_control_panel()
        
        top_bar.modeChanged.connect(self._on_mode_changed)
        control_panel.routing_editor.routingChanged.connect(self._on_routing_changed)
        
        center_panel.drop_zone.fileDropped.connect(self._on_file_dropped)
        right_panel.chat_widget.messageSent.connect(self._on_chat_message)
    
    def _setup_workspace(self):
        workspace = Path.home() / "AIWorkspace"
        workspace.mkdir(parents=True, exist_ok=True)
        
        folders = [
            {"name": "Documents", "path": str(workspace / "Documents")},
            {"name": "Images", "path": str(workspace / "Images")},
            {"name": "Code", "path": str(workspace / "Code")},
            {"name": "Downloads", "path": str(workspace / "Downloads")},
            {"name": "Archive", "path": str(workspace / "Archive")}
        ]
        
        for folder in folders:
            Path(folder["path"]).mkdir(parents=True, exist_ok=True)
        
        self.main_window.get_left_panel().set_folders(folders)
        self._update_memory_stats()
    
    def _on_mode_changed(self, mode: str):
        self.agent.developer_mode = (mode == "developer")
        self.main_window.get_center_panel().add_log(f"Mode changed to {mode}", "info")
    
    def _on_routing_changed(self, task_type: str, provider_name: str):
        from .llm import TaskType
        try:
            task_enum = TaskType(task_type)
            self.llm_router.update_task_routing(task_enum, provider_name)
            self.main_window.get_center_panel().add_log(f"Routing updated: {task_type} → {provider_name}", "success")
        except ValueError:
            pass
    
    def _on_file_dropped(self, file_path: str):
        print(f"[DEBUG] File dropped: {file_path}")
        
        try:
            self.main_window.get_center_panel().add_log(f"File dropped: {file_path}", "info")
            self.main_window.get_center_panel().set_processing_status("Processing file...", 10)
        except Exception as e:
            print(f"[ERROR] Failed to update UI: {e}")
            return
        
        async def process_file():
            try:
                print(f"[DEBUG] Starting file processing...")
                async for result in self.agent.process_file(file_path):
                    print(f"[DEBUG] Result type: {result['type']}")
                    
                    try:
                        if result["type"] == "status":
                            self.main_window.get_center_panel().add_log(result["message"], "thinking")
                            progress = {
                                "Extracting file metadata...": 20,
                                "Reading memory context...": 40,
                                "Planning action...": 60,
                                "Executing plan...": 80
                            }.get(result["message"], 50)
                            self.main_window.get_center_panel().set_processing_status(result["message"], progress)
                        
                        elif result["type"] == "plan":
                            self.main_window.get_center_panel().add_log(
                                f"Plan: {result['intent']} → {result['task_type']} (confidence: {result['confidence']:.0%})",
                                "info"
                            )
                        
                        elif result["type"] == "tool_result":
                            self.main_window.get_center_panel().add_log(f"Tool executed: {result['tool']}", "success")
                        
                        elif result["type"] == "llm_response":
                            self.main_window.get_center_panel().add_log(
                                f"LLM response: {result['task_type']} ({result['latency']:.2f}s)",
                                "success"
                            )
                            self._add_activity_log(result)
                        
                        elif result["type"] == "confirmation_required":
                            self.main_window.get_center_panel().add_log(f"Low confidence - requires confirmation", "warning")
                            self.main_window.get_center_panel().set_processing_status("Waiting for confirmation...", 85)
                        
                        elif result["type"] == "complete":
                            self.main_window.get_center_panel().add_log("Processing complete", "success")
                            self.main_window.get_center_panel().set_processing_status("Complete", 100)
                            self._update_memory_stats()
                            self._update_control_panel()
                    
                    except Exception as e:
                        print(f"[ERROR] Failed to process result: {e}")
                        import traceback
                        traceback.print_exc()
                
                from PySide6.QtCore import QTimer
                QTimer.singleShot(2000, self.main_window.get_center_panel().reset_processing)
                print(f"[DEBUG] File processing completed")
                
            except Exception as e:
                print(f"[ERROR] Error processing file: {e}")
                import traceback
                traceback.print_exc()
                try:
                    self.main_window.get_center_panel().add_log(f"Error processing file: {str(e)}", "error")
                    self.main_window.get_center_panel().reset_processing()
                except:
                    pass
        
        try:
            worker = AsyncWorker(process_file())
            worker.error.connect(lambda err: (
                print(f"[ERROR] Worker error: {err}"),
                self.main_window.get_center_panel().add_log(f"Error: {err}", "error")
            ))
            worker.finished.connect(lambda: print(f"[DEBUG] Worker finished"))
            worker.start()
            print(f"[DEBUG] Worker started")
        except Exception as e:
            print(f"[ERROR] Failed to start worker: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_chat_message(self, message: str):
        self.main_window.get_right_panel().add_chat_message(message, is_user=True)
        
        async def process_chat():
            try:
                async for result in self.agent.process_chat(message):
                    if result["type"] == "status":
                        self.main_window.get_center_panel().add_log(result["message"], "thinking")
                    
                    elif result["type"] == "plan":
                        self.main_window.get_center_panel().add_log(
                            f"Plan: {result['intent']} → {result['task_type']}",
                            "info"
                        )
                    
                    elif result["type"] == "llm_chunk":
                        self.main_window.get_right_panel().append_streaming_response(result["content"])
                    
                    elif result["type"] == "llm_response":
                        self.main_window.get_center_panel().add_log(
                            f"LLM response: {result['task_type']} ({result['latency']:.2f}s)",
                            "success"
                        )
                        self._add_activity_log(result)
                
            except Exception as e:
                self.main_window.get_center_panel().add_log(f"Error: {str(e)}", "error")
        
        worker = AsyncWorker(process_chat())
        worker.error.connect(lambda err: self.main_window.get_center_panel().add_log(f"Error: {err}", "error"))
        worker.start()
    
    def _add_activity_log(self, result: dict):
        entry = {
            "timestamp": result.get("timestamp", ""),
            "task_type": result.get("task_type", "unknown"),
            "provider": result.get("model", "unknown").split("-")[0],
            "latency": result.get("latency", 0),
            "tokens": result.get("usage", {}).get("total_tokens", 0),
            "cost": result.get("usage", {}).get("cost", 0),
            "success": True
        }
        self.main_window.add_activity_log(entry)
    
    def _update_memory_stats(self):
        stats = self.memory_system.get_stats()
        self.main_window.get_left_panel().update_memory_stats(stats)
    
    def _update_control_panel(self):
        routing = self.llm_router.get_task_routing()
        stats = self.llm_router.get_stats()
        
        self.main_window.update_control_panel(
            routing=routing,
            stats={
                "total_requests": stats.total_requests,
                "total_cost": stats.total_cost,
                "total_tokens": stats.total_tokens,
                "avg_latency": stats.avg_latency,
                "success_rate": stats.success_rate
            }
        )
    
    def run(self):
        self.main_window.show()
        return self.app.exec()
    
    def cleanup(self):
        pass


def main():
    application = Application()
    app = application.initialize()
    
    try:
        exit_code = application.run()
    finally:
        application.cleanup()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
