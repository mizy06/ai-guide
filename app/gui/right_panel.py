from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QTextCursor
from .theme import Theme


class ChatWidget(QWidget):
    messageSent = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("AI Chat")
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
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        
        scroll.setWidget(self.chat_container)
        layout.addWidget(scroll, 1)
        
        input_container = QFrame()
        input_container.setStyleSheet(f"background-color: {Theme.PANEL_BG.name()}; border-top: 1px solid {Theme.BORDER.name()};")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)
        
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(80)
        self.input_field.setPlaceholderText("Type your message...")
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.CARD_BG.name()};
                border: 1px solid {Theme.BORDER.name()};
                border-radius: 6px;
                padding: 8px;
                color: {Theme.TEXT_PRIMARY.name()};
            }}
            QTextEdit:focus {{
                border-color: {Theme.ACCENT_CYAN.name()};
            }}
        """)
        input_layout.addWidget(self.input_field)
        
        send_button = QPushButton("Send")
        send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_CYAN.name()};
                color: {Theme.DARK_BG.name()};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_PURPLE.name()};
            }}
        """)
        send_button.clicked.connect(self._send_message)
        input_layout.addWidget(send_button)
        
        layout.addWidget(input_container)
    
    def _send_message(self):
        text = self.input_field.toPlainText().strip()
        if text:
            self.add_message(text, is_user=True)
            self.input_field.clear()
            self.messageSent.emit(text)
    
    def add_message(self, text: str, is_user: bool = False):
        from datetime import datetime
        
        message_widget = QFrame()
        message_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.ACCENT_CYAN.name() if is_user else Theme.PANEL_BG.name()};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(4)
        
        sender_label = QLabel("You" if is_user else "AI")
        sender_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.DARK_BG.name() if is_user else Theme.ACCENT_CYAN.name()};
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        message_layout.addWidget(sender_label)
        
        content_label = QLabel(text)
        content_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.DARK_BG.name() if is_user else Theme.TEXT_PRIMARY.name()};
                font-size: 12px;
                word-wrap: true;
            }}
        """)
        content_label.setWordWrap(True)
        message_layout.addWidget(content_label)
        
        if is_user:
            message_widget.setMaximumWidth(300)
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message_widget)
    
    def append_streaming_response(self, text: str):
        last_widget = self.chat_layout.itemAt(self.chat_layout.count() - 2).widget()
        if last_widget:
            content_label = last_widget.findChild(QLabel)
            if content_label:
                current_text = content_label.text()
                content_label.setText(current_text + text)
    
    def clear(self):
        for i in reversed(range(self.chat_layout.count() - 1)):
            item = self.chat_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()


class FileUnderstandingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("File Understanding")
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
        
        self.file_name_label = QLabel("No file selected")
        self.file_name_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY.name()};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        content_layout.addWidget(self.file_name_label)
        
        self.file_type_label = QLabel("")
        self.file_type_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY.name()};
                font-size: 12px;
            }}
        """)
        content_layout.addWidget(self.file_type_label)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {Theme.BORDER.name()};")
        content_layout.addWidget(separator)
        
        confidence_label = QLabel("Confidence")
        confidence_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY.name()};
                font-size: 11px;
            }}
        """)
        content_layout.addWidget(confidence_label)
        
        self.confidence_value = QLabel("0%")
        self.confidence_value.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_CYAN.name()};
                font-size: 28px;
                font-weight: bold;
            }}
        """)
        content_layout.addWidget(self.confidence_value)
        
        reasoning_label = QLabel("Reasoning")
        reasoning_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY.name()};
                font-size: 11px;
            }}
        """)
        content_layout.addWidget(reasoning_label)
        
        self.reasoning_text = QLabel("")
        self.reasoning_text.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY.name()};
                font-size: 12px;
                padding: 10px;
                background-color: {Theme.PANEL_BG.name()};
                border-radius: 6px;
            }}
        """)
        self.reasoning_text.setWordWrap(True)
        content_layout.addWidget(self.reasoning_text)
        
        content_layout.addStretch()
        
        layout.addWidget(content)
    
    def update_file_info(self, file_name: str, file_type: str, confidence: float, reasoning: str):
        self.file_name_label.setText(file_name)
        self.file_type_label.setText(f"Type: {file_type}")
        self.confidence_value.setText(f"{confidence:.0%}")
        self.reasoning_text.setText(reasoning)
    
    def clear(self):
        self.file_name_label.setText("No file selected")
        self.file_type_label.setText("")
        self.confidence_value.setText("0%")
        self.reasoning_text.setText("")


class RightPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.chat_widget = ChatWidget()
        self.file_understanding = FileUnderstandingWidget()
        
        layout.addWidget(self.chat_widget, 2)
        layout.addWidget(self.file_understanding, 1)
    
    def add_chat_message(self, text: str, is_user: bool = False):
        self.chat_widget.add_message(text, is_user)
    
    def append_streaming_response(self, text: str):
        self.chat_widget.append_streaming_response(text)
    
    def update_file_understanding(self, file_name: str, file_type: str, confidence: float, reasoning: str):
        self.file_understanding.update_file_info(file_name, file_type, confidence, reasoning)
    
    def clear_file_understanding(self):
        self.file_understanding.clear()
