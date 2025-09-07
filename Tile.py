from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
import Workspace  # import the class, not the module


class Tile(QWidget):
    def __init__(self, urls=None):
        super().__init__()
        self.setObjectName("Tile")
        self.setProperty("isActiveTile", False)

        self.setFocusPolicy(Qt.StrongFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tabs)

        self.on_empty = None  # Workspace will assign this callback

        # Default tab behavior
        if urls is None:
            urls = ["https://www.google.com"]   # default
        for url in urls:
            self.add_tab(url)

        self.update_stylesheet(False)

    # ---------------- Events ----------------
    def mousePressEvent(self, event):
        # Walk up until we find a parent with "set_active_tile"
        parent = self.parentWidget()
        while parent is not None and not hasattr(parent, "set_active_tile"):
            parent = parent.parentWidget()
        if parent is not None and hasattr(parent, "set_active_tile"):
            parent.set_active_tile(self)
        super().mousePressEvent(event)

    # ---------------- Tabs ----------------
    def add_tab(self, url="https://www.google.com"):
        browser = QWebEngineView()
        browser.setUrl(QUrl(url))
        tab_index = self.tabs.addTab(browser, QUrl(url).host() or "New Tab")
        self.tabs.setCurrentIndex(tab_index)
        if self.property("isActiveTile"):
            browser.setFocus()
        return tab_index

    def close_tab(self, index: int):
        """Close the tab at index, and remove tile if none remain."""
        if index < 0 or index >= self.tabs.count():
            return
        w = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if w:
            w.deleteLater()

        # If no tabs remain, tell Workspace to remove this tile
        if self.tabs.count() == 0 and callable(self.on_empty):
            self.on_empty()

    def go_back(self):
        current_browser = self.tabs.currentWidget()
        if current_browser and current_browser.history().canGoBack():
            current_browser.back()

    def go_forward(self):
        current_browser = self.tabs.currentWidget()
        if current_browser and current_browser.history().canGoForward():
            current_browser.forward()

    # ---------------- Styling ----------------
    def update_stylesheet(self, is_active: bool):
        self.setProperty("isActiveTile", is_active)
        if is_active:
            self.setStyleSheet("""
                #Tile {
                    border: 5px solid #00aaff;
                    border-radius: 8px;
                    background-color: rgba(70, 70, 70, 230);
                }
                QTabWidget::pane { border: 2px solid #00aaff; }
                QTabBar::tab:selected { background-color: #00aaff; color: white; }
            """)
        else:
            self.setStyleSheet("""
                #Tile {
                    border: 5px solid transparent;
                    border-radius: 8px;
                    background-color: rgba(50, 50, 50, 200);
                }
                QTabWidget::pane { border: 2px solid transparent; }
                QTabBar::tab:selected { background-color: #444; color: white; }
            """)

    def on_tab_changed(self, index):
        if self.property("isActiveTile"):
            current_browser = self.tabs.currentWidget()
            if current_browser:
                current_browser.setFocus()

    # ---------------- Persistence ----------------
    def to_dict(self):
        urls = []
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if view:
                url = view.url().toString()
                if url:
                    urls.append(url)
        return {"tabs": urls}

    def load_from_dict(self, data):
        self.tabs.clear()
        for url in data.get("tabs", []) or []:
            self.add_tab(url)