from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class Theme:
    DARK_BG = QColor(10, 10, 15)
    PANEL_BG = QColor(18, 18, 25)
    CARD_BG = QColor(25, 25, 35)
    TEXT_PRIMARY = QColor(240, 240, 245)
    TEXT_SECONDARY = QColor(150, 150, 160)
    ACCENT_CYAN = QColor(0, 212, 255)
    ACCENT_PURPLE = QColor(138, 43, 226)
    SUCCESS = QColor(0, 200, 100)
    WARNING = QColor(255, 180, 0)
    ERROR = QColor(255, 80, 80)
    BORDER = QColor(50, 50, 70)
    
    @staticmethod
    def apply_dark_theme(app: QApplication):
        palette = app.palette()
        
        palette.setColor(QPalette.Window, Theme.DARK_BG)
        palette.setColor(QPalette.WindowText, Theme.TEXT_PRIMARY)
        palette.setColor(QPalette.Base, Theme.PANEL_BG)
        palette.setColor(QPalette.AlternateBase, Theme.CARD_BG)
        palette.setColor(QPalette.ToolTipBase, Theme.TEXT_PRIMARY)
        palette.setColor(QPalette.ToolTipText, Theme.TEXT_PRIMARY)
        palette.setColor(QPalette.Text, Theme.TEXT_PRIMARY)
        palette.setColor(QPalette.Button, Theme.CARD_BG)
        palette.setColor(QPalette.ButtonText, Theme.TEXT_PRIMARY)
        palette.setColor(QPalette.BrightText, Theme.ACCENT_CYAN)
        palette.setColor(QPalette.Link, Theme.ACCENT_CYAN)
        palette.setColor(QPalette.Highlight, Theme.ACCENT_CYAN)
        palette.setColor(QPalette.HighlightedText, Theme.DARK_BG)
        
        app.setPalette(palette)
        app.setStyle("Fusion")


class ThemeManager(QObject):
    themeChanged = Signal()
    
    def __init__(self):
        super().__init__()
        self._current_theme = "dark"
    
    def set_theme(self, theme_name: str):
        self._current_theme = theme_name
        self.themeChanged.emit()
    
    def get_stylesheet(self) -> str:
        return f"""
        QMainWindow {{
            background-color: {Theme.DARK_BG.name()};
        }}
        
        QWidget {{
            background-color: transparent;
            color: {Theme.TEXT_PRIMARY.name()};
            font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
            font-size: 13px;
        }}
        
        QFrame {{
            background-color: {Theme.PANEL_BG.name()};
            border: 1px solid {Theme.BORDER.name()};
            border-radius: 8px;
        }}
        
        QPushButton {{
            background-color: {Theme.CARD_BG.name()};
            border: 1px solid {Theme.BORDER.name()};
            border-radius: 6px;
            padding: 8px 16px;
            color: {Theme.TEXT_PRIMARY.name()};
        }}
        
        QPushButton:hover {{
            background-color: {Theme.ACCENT_CYAN.name()};
            color: {Theme.DARK_BG.name()};
            border-color: {Theme.ACCENT_CYAN.name()};
        }}
        
        QPushButton:pressed {{
            background-color: {Theme.ACCENT_PURPLE.name()};
        }}
        
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {Theme.CARD_BG.name()};
            border: 1px solid {Theme.BORDER.name()};
            border-radius: 6px;
            padding: 8px;
            color: {Theme.TEXT_PRIMARY.name()};
            selection-background-color: {Theme.ACCENT_CYAN.name()};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {Theme.ACCENT_CYAN.name()};
        }}
        
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        
        QScrollBar:vertical {{
            background-color: {Theme.PANEL_BG.name()};
            width: 10px;
            border-radius: 5px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {Theme.BORDER.name()};
            border-radius: 5px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {Theme.ACCENT_CYAN.name()};
        }}
        
        QScrollBar:horizontal {{
            background-color: {Theme.PANEL_BG.name()};
            height: 10px;
            border-radius: 5px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {Theme.BORDER.name()};
            border-radius: 5px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {Theme.ACCENT_CYAN.name()};
        }}
        
        QTreeWidget {{
            background-color: {Theme.CARD_BG.name()};
            border: 1px solid {Theme.BORDER.name()};
            border-radius: 6px;
        }}
        
        QTreeWidget::item {{
            padding: 6px;
            border-bottom: 1px solid {Theme.BORDER.name()};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {Theme.ACCENT_CYAN.name()};
            color: {Theme.DARK_BG.name()};
        }}
        
        QTreeWidget::item:hover {{
            background-color: {Theme.CARD_BG.name()};
        }}
        
        QComboBox {{
            background-color: {Theme.CARD_BG.name()};
            border: 1px solid {Theme.BORDER.name()};
            border-radius: 6px;
            padding: 6px 12px;
            color: {Theme.TEXT_PRIMARY.name()};
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
        
        QLabel {{
            color: {Theme.TEXT_PRIMARY.name()};
        }}
        
        QProgressBar {{
            background-color: {Theme.CARD_BG.name()};
            border: 1px solid {Theme.BORDER.name()};
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {Theme.ACCENT_CYAN.name()};
            border-radius: 3px;
        }}
        
        QTabWidget::pane {{
            border: 1px solid {Theme.BORDER.name()};
            background-color: {Theme.PANEL_BG.name()};
            border-radius: 8px;
        }}
        
        QTabBar::tab {{
            background-color: {Theme.CARD_BG.name()};
            color: {Theme.TEXT_SECONDARY.name()};
            padding: 10px 20px;
            border: 1px solid {Theme.BORDER.name()};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {Theme.PANEL_BG.name()};
            color: {Theme.ACCENT_CYAN.name()};
            border-color: {Theme.ACCENT_CYAN.name()};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {Theme.ACCENT_PURPLE.name()};
            color: {Theme.TEXT_PRIMARY.name()};
        }}
        
        QSplitter::handle {{
            background-color: {Theme.BORDER.name()};
        }}
        
        QSplitter::handle:hover {{
            background-color: {Theme.ACCENT_CYAN.name()};
        }}
        """
