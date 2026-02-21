from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QScrollArea, QProgressBar, QPushButton
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from typing import Dict, Any
from .theme import Theme


class ModelRoutingEditor(QWidget):
    routingChanged = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("Model Routing")
        header.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_CYAN.name()};
                font-weight: bold;
                font-size: 14px;
                padding: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PANEL_BG.name()}, stop:1 {Theme.CARD_BG.name()});
                border-bottom: 1px solid {Theme.BORDER.name()};
            }}
        """)
        layout.addWidget(header)
        
        content = QFrame()
        content.setStyleSheet(f"background-color: {Theme.CARD_BG.name()};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(12)
        
        self.routing_widgets = {}
        
        task_configs = [
            ("classify", "File Classification", "Fast & cheap"),
            ("decision", "Decision Making", "Strong reasoning"),
            ("summarize", "Document Summary", "Long context"),
            ("codegen", "Code Generation", "Best coding"),
            ("chat", "General Chat", "Balanced")
        ]
        
        for task_key, task_name, task_desc in task_configs:
            row = self._create_routing_row(task_key, task_name, task_desc)
            content_layout.addWidget(row)
        
        content_layout.addStretch()
        layout.addWidget(content)
    
    def _create_routing_row(self, task_key: str, task_name: str, task_desc: str) -> QWidget:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        name_label = QLabel(task_name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY.name()};
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        info_layout.addWidget(name_label)
        
        desc_label = QLabel(task_desc)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY.name()};
                font-size: 11px;
            }}
        """)
        info_layout.addWidget(desc_label)
        
        row_layout.addLayout(info_layout, 1)
        
        combo = QComboBox()
        combo.addItems(["deepseek", "doubao", "tongyi", "zhipu", "baichuan", "wenxin"])
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.PANEL_BG.name()};
                border: 1px solid {Theme.BORDER.name()};
                border-radius: 6px;
                padding: 6px 12px;
                color: {Theme.TEXT_PRIMARY.name()};
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {Theme.ACCENT_CYAN.name()};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {Theme.TEXT_SECONDARY.name()};
            }}
        """)
        combo.currentTextChanged.connect(
            lambda provider, key=task_key: self.routingChanged.emit(key, provider)
        )
        
        self.routing_widgets[task_key] = combo
        row_layout.addWidget(combo)
        
        return row
    
    def update_routing(self, routing: Dict[str, str]):
        for task_key, provider_name in routing.items():
            if task_key in self.routing_widgets:
                combo = self.routing_widgets[task_key]
                index = combo.findText(provider_name)
                if index >= 0:
                    combo.setCurrentIndex(index)


class LiveActivityConsole(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("Live Activity")
        header.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_CYAN.name()};
                font-weight: bold;
                font-size: 14px;
                padding: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PANEL_BG.name()}, stop:1 {Theme.CARD_BG.name()});
                border-bottom: 1px solid {Theme.BORDER.name()};
            }}
        """)
        layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {Theme.CARD_BG.name()};
            }}
        """)
        
        self.console_container = QWidget()
        self.console_layout = QVBoxLayout(self.console_container)
        self.console_layout.setContentsMargins(10, 10, 10, 10)
        self.console_layout.setSpacing(6)
        self.console_layout.addStretch()
        
        scroll.setWidget(self.console_container)
        layout.addWidget(scroll)
    
    def add_log_entry(self, entry: Dict[str, Any]):
        from datetime import datetime
        
        timestamp = entry.get("timestamp", datetime.now().strftime("%H:%M:%S"))
        provider = entry.get("provider", "unknown")
        task_type = entry.get("task_type", "unknown")
        latency = entry.get("latency", 0)
        tokens = entry.get("tokens", 0)
        cost = entry.get("cost", 0)
        success = entry.get("success", True)
        
        color = Theme.SUCCESS if success else Theme.ERROR
        
        log_widget = QFrame()
        log_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.PANEL_BG.name()};
                border-left: 3px solid {color.name()};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        
        log_layout = QHBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(10)
        
        info_text = f"[{timestamp}] [{provider.upper()}] {task_type}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY.name()};
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        log_layout.addWidget(info_label)
        
        log_layout.addStretch()
        
        stats_text = f"{latency*1000:.0f}ms | {tokens} tokens | ${cost:.6f}"
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY.name()};
                font-size: 10px;
            }}
        """)
        log_layout.addWidget(stats_label)
        
        self.console_layout.insertWidget(self.console_layout.count() - 1, log_widget)
        
        if self.console_layout.count() > 50:
            item = self.console_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
    
    def clear(self):
        for i in reversed(range(self.console_layout.count() - 1)):
            item = self.console_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()


class StatsDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.total_requests_value_label = None
        self.total_cost_value_label = None
        self.total_tokens_value_label = None
        self.avg_latency_value_label = None
        self.success_rate_value_label = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("Statistics")
        header.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_CYAN.name()};
                font-weight: bold;
                font-size: 14px;
                padding: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PANEL_BG.name()}, stop:1 {Theme.CARD_BG.name()});
                border-bottom: 1px solid {Theme.BORDER.name()};
            }}
        """)
        layout.addWidget(header)
        
        content = QFrame()
        content.setStyleSheet(f"background-color: {Theme.CARD_BG.name()};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        self.total_requests_label = self._create_stat_item("Total Requests", "0")
        self.total_requests_value_label = self.total_requests_label.findChild(QLabel, "value")
        
        self.total_cost_label = self._create_stat_item("Total Cost", "$0.00")
        self.total_cost_value_label = self.total_cost_label.findChild(QLabel, "value")
        
        self.total_tokens_label = self._create_stat_item("Total Tokens", "0")
        self.total_tokens_value_label = self.total_tokens_label.findChild(QLabel, "value")
        
        self.avg_latency_label = self._create_stat_item("Avg Latency", "0ms")
        self.avg_latency_value_label = self.avg_latency_label.findChild(QLabel, "value")
        
        self.success_rate_label = self._create_stat_item("Success Rate", "100%")
        self.success_rate_value_label = self.success_rate_label.findChild(QLabel, "value")
        
        content_layout.addWidget(self.total_requests_label)
        content_layout.addWidget(self.total_cost_label)
        content_layout.addWidget(self.total_tokens_label)
        content_layout.addWidget(self.avg_latency_label)
        content_layout.addWidget(self.success_rate_label)
        content_layout.addStretch()
        
        layout.addWidget(content)
    
    def _create_stat_item(self, title: str, value: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY.name()};
                font-size: 11px;
            }}
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_CYAN.name()};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(value_label)
        
        return widget
    
    def update_stats(self, stats: Dict[str, Any]):
        total_requests = stats.get("total_requests", 0)
        total_cost = stats.get("total_cost", 0.0)
        total_tokens = stats.get("total_tokens", 0)
        avg_latency = stats.get("avg_latency", 0.0)
        success_rate = stats.get("success_rate", 1.0)
        
        if self.total_requests_value_label:
            self.total_requests_value_label.setText(str(total_requests))
        if self.total_cost_value_label:
            self.total_cost_value_label.setText(f"${total_cost:.4f}")
        if self.total_tokens_value_label:
            self.total_tokens_value_label.setText(str(total_tokens))
        if self.avg_latency_value_label:
            self.avg_latency_value_label.setText(f"{avg_latency*1000:.0f}ms")
        if self.success_rate_value_label:
            self.success_rate_value_label.setText(f"{success_rate:.1%}")


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.routing_editor = ModelRoutingEditor()
        self.activity_console = LiveActivityConsole()
        self.stats_dashboard = StatsDashboard()
        
        layout.addWidget(self.routing_editor, 1)
        layout.addWidget(self.activity_console, 2)
        layout.addWidget(self.stats_dashboard, 1)
    
    def update_routing(self, routing: Dict[str, str]):
        self.routing_editor.update_routing(routing)
    
    def add_activity_log(self, entry: Dict[str, Any]):
        self.activity_console.add_log_entry(entry)
    
    def update_stats(self, stats: Dict[str, Any]):
        self.stats_dashboard.update_stats(stats)
    
    def clear_activity(self):
        self.activity_console.clear()
