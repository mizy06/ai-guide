from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from .theme import Theme


class DropZoneWidget(QFrame):
    fileDropped = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._is_dragging = False
        self.setAcceptDrops(True)
    
    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel)
        self.setMinimumHeight(200)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.CARD_BG.name()};
                border: 2px dashed {Theme.BORDER.name()};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {Theme.ACCENT_CYAN.name()};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel()
        icon_label.setText("📁")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        text_label = QLabel("Drop files here to organize")
        text_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY.name()};
            font-size: 16px;
            font-weight: 500;
        """)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
        sub_label = QLabel("AI will analyze and classify automatically")
        sub_label.setStyleSheet(f"""
            color: {Theme.TEXT_SECONDARY.name()};
            font-size: 12px;
            opacity: 0.7;
        """)
        sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub_label)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._is_dragging = True
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.ACCENT_CYAN.name()};
                    border: 2px solid {Theme.ACCENT_CYAN.name()};
                    border-radius: 12px;
                }}
            """)
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        self._is_dragging = False
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.CARD_BG.name()};
                border: 2px dashed {Theme.BORDER.name()};
                border-radius: 12px;
            }}
        """)
    
    def dropEvent(self, event):
        self._is_dragging = False
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.CARD_BG.name()};
                border: 2px dashed {Theme.BORDER.name()};
                border-radius: 12px;
            }}
        """)
        
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.fileDropped.emit(file_path)


class ActivityLogWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("Activity Log")
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
        
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(10, 10, 10, 10)
        self.log_layout.setSpacing(8)
        self.log_layout.addStretch()
        
        scroll.setWidget(self.log_container)
        layout.addWidget(scroll)
    
    def add_log(self, message: str, log_type: str = "info"):
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "info": Theme.ACCENT_CYAN,
            "success": Theme.SUCCESS,
            "warning": Theme.WARNING,
            "error": Theme.ERROR,
            "thinking": Theme.ACCENT_PURPLE
        }
        
        color = colors.get(log_type, Theme.TEXT_SECONDARY)
        
        log_entry = QLabel(f"[{timestamp}] {message}")
        log_entry.setStyleSheet(f"""
            QLabel {{
                color: {color.name()};
                font-size: 12px;
                padding: 6px;
                background-color: {Theme.PANEL_BG.name()};
                border-radius: 4px;
                border-left: 3px solid {color.name()};
            }}
        """)
        log_entry.setWordWrap(True)
        
        self.log_layout.insertWidget(self.log_layout.count() - 1, log_entry)
    
    def clear(self):
        for i in reversed(range(self.log_layout.count() - 1)):
            item = self.log_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()


class ProcessingIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self._progress = 0
        self._status = "Ready"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.status_label = QLabel(self._status)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_CYAN.name()};
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.PANEL_BG.name()};
                border: 1px solid {Theme.BORDER.name()};
                border-radius: 6px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.ACCENT_CYAN.name()}, stop:1 {Theme.ACCENT_PURPLE.name()});
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.progress_bar)
    
    def set_status(self, status: str, progress: int = 0):
        self._status = status
        self._progress = progress
        self.status_label.setText(status)
        self.progress_bar.setValue(progress)
    
    def reset(self):
        self.set_status("Ready", 0)


class CenterPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.drop_zone = DropZoneWidget()
        self.processing_indicator = ProcessingIndicator()
        self.activity_log = ActivityLogWidget()
        
        layout.addWidget(self.drop_zone, 1)
        layout.addWidget(self.processing_indicator)
        layout.addWidget(self.activity_log, 1)
    
    def add_log(self, message: str, log_type: str = "info"):
        self.activity_log.add_log(message, log_type)
    
    def set_processing_status(self, status: str, progress: int = 0):
        self.processing_indicator.set_status(status, progress)
    
    def reset_processing(self):
        self.processing_indicator.reset()
