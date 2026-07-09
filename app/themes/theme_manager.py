from typing import Optional, Callable
from PySide6.QtGui import QColor
from app.themes.theme_definitions import ThemeDefinition, get_theme, list_themes


class ThemeManager:
    """Manages theme application and stylesheet generation."""

    def __init__(self):
        """Initialize theme manager."""
        self.current_theme: Optional[ThemeDefinition] = None
        self._observers: list[Callable[[ThemeDefinition], None]] = []

    def set_theme(self, theme_name: str) -> bool:
        """Set current theme by name."""
        theme = get_theme(theme_name)
        if not theme:
            return False
        self.current_theme = theme
        self._notify_observers()
        return True

    def get_current_theme(self) -> Optional[ThemeDefinition]:
        """Get current theme."""
        return self.current_theme

    def get_available_themes(self) -> list[str]:
        """Get list of available theme names."""
        return list_themes()

    def subscribe(self, callback: Callable[[ThemeDefinition], None]) -> None:
        """Subscribe to theme changes."""
        self._observers.append(callback)

    def unsubscribe(self, callback: Callable[[ThemeDefinition], None]) -> None:
        """Unsubscribe from theme changes."""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> None:
        """Notify all observers of theme change."""
        if self.current_theme:
            for observer in self._observers:
                observer(self.current_theme)

    def generate_stylesheet(self) -> str:
        """Generate QSS stylesheet from current theme."""
        if not self.current_theme:
            return ""

        ui = self.current_theme.ui
        return f"""
            * {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
                font-size: 12px;
            }}

            QMainWindow {{
                background-color: {ui.background};
                color: {ui.foreground};
            }}

            QWidget {{
                background-color: {ui.background};
                color: {ui.foreground};
            }}

            QMenuBar {{
                background-color: {ui.background};
                color: {ui.foreground};
                border-bottom: 1px solid {ui.border};
                padding: 2px 4px;
            }}

            QMenuBar::item {{
                padding: 4px 12px;
                background-color: transparent;
            }}

            QMenuBar::item:selected {{
                background-color: {ui.hover};
                color: {ui.foreground};
                border-radius: 4px;
            }}

            QMenu {{
                background-color: {ui.background};
                color: {ui.foreground};
                border: 1px solid {ui.border};
                border-radius: 4px;
                padding: 4px 0px;
            }}

            QMenu::item {{
                padding: 6px 20px;
            }}

            QMenu::item:selected {{
                background-color: {ui.selection};
                color: {ui.foreground};
                border-radius: 0px;
            }}

            QToolBar {{
                background-color: {ui.background};
                border-bottom: 1px solid {ui.border};
                padding: 4px;
                spacing: 4px;
            }}

            QToolBar::separator {{
                background-color: {ui.border};
                width: 1px;
                margin: 4px 2px;
            }}

            QPushButton {{
                background-color: {ui.accent};
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: 500;
                font-size: 12px;
            }}

            QPushButton:hover {{
                background-color: {ui.accent_alt};
            }}

            QPushButton:pressed {{
                background-color: {ui.accent_alt};
                margin: 1px 0px -1px 0px;
            }}

            QPushButton:disabled {{
                background-color: {ui.border};
                color: {ui.foreground};
                opacity: 0.5;
            }}

            QLineEdit {{
                background-color: {ui.background};
                color: {ui.foreground};
                border: 1px solid {ui.border};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }}

            QLineEdit:focus {{
                border: 2px solid {ui.accent};
                padding: 5px 7px;
            }}

            QComboBox {{
                background-color: {ui.background};
                color: {ui.foreground};
                border: 1px solid {ui.border};
                border-radius: 4px;
                padding: 5px 6px;
                padding-right: 26px;
                font-size: 12px;
                min-height: 24px;
            }}

            QComboBox:focus {{
                border: 2px solid {ui.accent};
                outline: none;
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border: none;
                background-color: transparent;
            }}

            QComboBox::drop-down:hover {{
                background-color: {ui.hover};
                color: {ui.foreground};
            }}

            QComboBox::down-arrow {{
                width: 12px;
                height: 8px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {ui.background};
                color: {ui.foreground};
                selection-background-color: {ui.selection};
                border: 1px solid {ui.border};
                border-radius: 2px;
                outline: none;
                margin: 0px;
                padding: 2px 0px;
            }}

            QComboBox QAbstractItemView::item {{
                padding: 6px 8px;
                height: 24px;
            }}

            QComboBox QAbstractItemView::item:hover {{
                background-color: {ui.hover};
            }}

            QComboBox QAbstractItemView::item:selected {{
                background-color: {ui.selection};
                color: {ui.foreground};
            }}

            QLabel {{
                color: {ui.foreground};
                font-size: 12px;
            }}

            QTreeWidget {{
                background-color: {ui.background};
                color: {ui.foreground};
                border: 1px solid {ui.border};
                border-radius: 4px;
                gridline-color: {ui.border};
            }}

            QTreeWidget::item {{
                padding: 4px 2px;
                height: 24px;
            }}

            QTreeWidget::item:hover {{
                background-color: {ui.hover};
                color: {ui.foreground};
                border-radius: 2px;
            }}

            QTreeWidget::item:selected {{
                background-color: {ui.selection};
                color: {ui.foreground};
                border-radius: 2px;
            }}

            QPlainTextEdit {{
                background-color: {ui.background};
                color: {ui.foreground};
                border: 1px solid {ui.border};
                border-radius: 4px;
                padding: 6px;
                font-family: "Courier New", Courier, monospace;
                font-size: 12px;
            }}

            QTextEdit {{
                background-color: {ui.background};
                color: {ui.foreground};
                border: 1px solid {ui.border};
                border-radius: 4px;
                padding: 6px;
                font-family: "Courier New", Courier, monospace;
                font-size: 12px;
            }}

            QStatusBar {{
                background-color: {ui.background};
                color: {ui.foreground};
                border-top: 1px solid {ui.border};
                padding: 4px 8px;
            }}

            QSplitter::handle {{
                background-color: {ui.border};
                width: 5px;
                height: 5px;
            }}

            QSplitter::handle:hover {{
                background-color: {ui.hover};
            }}

            QTabBar {{
                background-color: {ui.background};
                border-bottom: 1px solid {ui.border};
            }}

            QTabBar::tab {{
                background-color: {ui.hover};
                color: {ui.foreground};
                padding: 8px 16px;
                border: 1px solid {ui.border};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-size: 12px;
            }}

            QTabBar::tab:selected {{
                background-color: {ui.accent};
                color: #FFFFFF;
                border: 1px solid {ui.accent};
                border-bottom: none;
            }}

            QTabBar::tab:hover:!selected {{
                background-color: {ui.selection};
            }}

            QTabWidget::pane {{
                border: 1px solid {ui.border};
                border-radius: 0px 0px 4px 4px;
            }}

            QScrollBar:vertical {{
                background-color: {ui.background};
                width: 12px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {ui.border};
                border-radius: 6px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {ui.hover};
            }}

            QScrollBar:horizontal {{
                background-color: {ui.background};
                height: 12px;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {ui.border};
                border-radius: 6px;
                min-width: 20px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {ui.hover};
            }}

            QScrollBar::add-line, QScrollBar::sub-line {{
                border: none;
                background-color: none;
            }}
        """

    def get_syntax_colors(self) -> dict[str, str]:
        """Get syntax highlighting colors."""
        if not self.current_theme:
            return {
                "keyword": "#0066CC",
                "builtin": "#666666",
                "string": "#CC0000",
                "comment": "#669966",
                "number": "#CC6600",
                "function": "#9B6432",
            }
        syntax = self.current_theme.syntax
        return {
            "keyword": syntax.keyword,
            "builtin": syntax.builtin,
            "string": syntax.string,
            "comment": syntax.comment,
            "number": syntax.number,
            "function": syntax.function,
        }

    def get_ui_colors(self) -> dict[str, str]:
        """Get UI colors."""
        if not self.current_theme:
            return {}
        ui = self.current_theme.ui
        return {
            "background": ui.background,
            "foreground": ui.foreground,
            "accent": ui.accent,
            "accent_alt": ui.accent_alt,
            "border": ui.border,
            "hover": ui.hover,
            "selection": ui.selection,
            "link": ui.link,
        }
