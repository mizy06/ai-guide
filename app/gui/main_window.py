from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon
from .theme import Theme, ThemeManager
from .left_panel import LeftPanel
from .center_panel import CenterPanel
from .right_panel import RightPanel
from .control_panel import ControlPanel


class TopBar(QWidget):
    modeChanged = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PANEL_BG.name()}, stop:1 {Theme.CARD_BG.name()});
                border-bottom: 1px solid {Theme.BORDER.name()};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(20)
        
        logo_label = QLabel("🤖 AI File Intelligence")
        logo_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_CYAN.name()};
                font-size: 18px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(logo_label)
        
        layout.addStretch()
        
        mode_container = QFrame()
        mode_container.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.CARD_BG.name()};
                border: 1px solid {Theme.BORDER.name()};
                border-radius: 6px;
            }}
        """)
        mode_layout = QHBoxLayout(mode_container)
        mode_layout.setContentsMargins(5, 5, 5, 5)
        mode_layout.setSpacing(5)
        
        user_mode_btn = QPushButton("User")
        user_mode_btn.setCheckable(True)
        user_mode_btn.setChecked(True)
        user_mode_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_CYAN.name()};
                color: {Theme.DARK_BG.name()};
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:!checked {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY.name()};
            }}
            QPushButton:hover:!checked {{
                color: {Theme.TEXT_PRIMARY.name()};
            }}
        """)
        user_mode_btn.clicked.connect(lambda: self._set_mode("user", user_mode_btn, dev_mode_btn))
        mode_layout.addWidget(user_mode_btn)
        
        dev_mode_btn = QPushButton("Developer")
        dev_mode_btn.setCheckable(True)
        dev_mode_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY.name()};
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {Theme.ACCENT_PURPLE.name()};
                color: {Theme.TEXT_PRIMARY.name()};
            }}
            QPushButton:hover:!checked {{
                color: {Theme.TEXT_PRIMARY.name()};
            }}
        """)
        dev_mode_btn.clicked.connect(lambda: self._set_mode("developer", dev_mode_btn, user_mode_btn))
        mode_layout.addWidget(dev_mode_btn)
        
        layout.addWidget(mode_container)
    
    def _set_mode(self, mode: str, checked_btn: QPushButton, unchecked_btn: QPushButton):
        checked_btn.setChecked(True)
        unchecked_btn.setChecked(False)
        self.modeChanged.emit(mode)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._apply_theme()
        self._setup_stats_timer()
    
    def _setup_ui(self):
        self.setWindowTitle("AI File Intelligence System")
        self.setMinimumSize(1600, 1000)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.top_bar = TopBar()
        main_layout.addWidget(self.top_bar)
        
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Theme.BORDER.name()};
                width: 1px;
            }}
        """)
        
        self.left_panel = LeftPanel()
        self.center_panel = CenterPanel()
        self.right_panel = RightPanel()
        self.control_panel = ControlPanel()
        
        content_splitter.addWidget(self.left_panel)
        content_splitter.addWidget(self.center_panel)
        content_splitter.addWidget(self.right_panel)
        content_splitter.addWidget(self.control_panel)
        
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setStretchFactor(2, 2)
        content_splitter.setStretchFactor(3, 2)
        
        main_layout.addWidget(content_splitter)
    
    def _apply_theme(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        Theme.apply_dark_theme(app)
        
        theme_manager = ThemeManager()
        self.setStyleSheet(theme_manager.get_stylesheet())
    
    def _setup_stats_timer(self):
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats_display)
        self.stats_timer.start(1000)
    
    def _update_stats_display(self):
        pass
    
    def get_top_bar(self) -> TopBar:
        return self.top_bar
    
    def get_left_panel(self) -> LeftPanel:
        return self.left_panel
    
    def get_center_panel(self) -> CenterPanel:
        return self.center_panel
    
    def get_right_panel(self) -> RightPanel:
        return self.right_panel
    
    def get_control_panel(self) -> ControlPanel:
        return self.control_panel
    
    def update_control_panel(self, routing: dict, stats: dict):
        self.control_panel.update_routing(routing)
        self.control_panel.update_stats(stats)
    
    def add_activity_log(self, entry: dict):
        self.control_panel.add_activity_log(entry)
