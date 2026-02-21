from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
    QTreeWidgetItem, QFrame, QProgressBar, QPushButton
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont
from .theme import Theme


class FolderTreeWidget(QWidget):
    folderSelected = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("Workspace")
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
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {Theme.CARD_BG.name()};
                border: none;
                border-radius: 0;
            }}
            QTreeWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {Theme.BORDER.name()};
            }}
            QTreeWidget::item:selected {{
                background-color: {Theme.ACCENT_CYAN.name()};
                color: {Theme.DARK_BG.name()};
            }}
            QTreeWidget::item:hover {{
                background-color: {Theme.ACCENT_PURPLE.name()};
                color: {Theme.TEXT_PRIMARY.name()};
            }}
        """)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)
    
    def _on_item_clicked(self, item, column):
        path = item.data(0, Qt.UserRole)
        if path:
            self.folderSelected.emit(path)
    
    def set_folders(self, folders: list):
        self.tree.clear()
        
        for folder in folders:
            item = QTreeWidgetItem([folder['name']])
            item.setData(0, Qt.UserRole, folder['path'])
            item.setIcon(0, self._get_folder_icon())
            self.tree.addTopLevelItem(item)
    
    def _get_folder_icon(self):
        from PySide6.QtGui import QIcon
        return QIcon()
    
    def get_selected_path(self) -> str:
        item = self.tree.currentItem()
        if item:
            return item.data(0, Qt.UserRole)
        return ""


class MemoryStatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.vector_value_label = None
        self.rule_value_label = None
        self.confidence_value_label = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("Memory Status")
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
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        self.vector_label = self._create_stat_label("Vector Entries", "0")
        self.vector_value_label = self.vector_label.findChild(QLabel, "value")
        
        self.rule_label = self._create_stat_label("Rules", "0")
        self.rule_value_label = self.rule_label.findChild(QLabel, "value")
        
        self.confidence_label = self._create_stat_label("Avg Confidence", "0%")
        self.confidence_value_label = self.confidence_label.findChild(QLabel, "value")
        
        content_layout.addWidget(self.vector_label)
        content_layout.addWidget(self.rule_label)
        content_layout.addWidget(self.confidence_label)
        content_layout.addStretch()
        
        layout.addWidget(content)
    
    def _create_stat_label(self, title: str, value: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY.name()}; font-size: 11px;")
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"""
            color: {Theme.ACCENT_CYAN.name()};
            font-size: 24px;
            font-weight: bold;
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return widget
    
    def update_stats(self, stats: dict):
        if self.vector_value_label:
            self.vector_value_label.setText(str(stats.get('vector_entries', 0)))
        if self.rule_value_label:
            self.rule_value_label.setText(str(stats.get('rule_count', 0)))
        if self.confidence_value_label:
            self.confidence_value_label.setText(f"{stats.get('avg_confidence', 0):.0%}")


class LeftPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.folder_tree = FolderTreeWidget()
        self.memory_status = MemoryStatusWidget()
        
        layout.addWidget(self.folder_tree, 2)
        layout.addWidget(self.memory_status, 1)
    
    def set_folders(self, folders: list):
        self.folder_tree.set_folders(folders)
    
    def update_memory_stats(self, stats: dict):
        self.memory_status.update_stats(stats)
