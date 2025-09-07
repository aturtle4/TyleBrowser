import json
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut, QIcon
from PySide6.QtCore import Qt, QUrl, QTimer
from Workspace import Workspace

SESSION_PATH = os.path.join(os.path.dirname(__file__), "session.json")


class TilingBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tyle Browser")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget { background-color: rgba(30, 30, 30, 220); color: white; }
            QPushButton { background-color: #444; color: white; border: none; padding: 6px; border-radius: 12px; min-width: 24px; }
            QPushButton:hover { background-color: #666; }
            QPushButton#minimizeBtn:hover { background-color: #f1c40f; }
            QPushButton#maximizeBtn:hover { background-color: #2ecc71; }
            QPushButton#closeBtn:hover { background-color: #e74c3c; }
            QPushButton.tilingBtn:checked { background-color: #00aaff; }
            QLineEdit { background-color: rgba(30, 30, 30, 230); color: white; border: 2px solid #00aaff; border-radius: 12px; padding: 8px 12px; font-size: 16px; }
        """)
        # self.setWindowIcon(QIcon(r"misc\Tylelogo.png"))
        self.setGeometry(0, 0, 1400, 900)
        self.setWindowState(Qt.WindowMaximized)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.topbar = QHBoxLayout()
        self.layout.addLayout(self.topbar)

        self.workspace_area = QVBoxLayout()
        self.layout.addLayout(self.workspace_area)

        self.workspaces = {}
        self.current_workspace = None
        self.current_workspace_idx = 1
        self.workspace_buttons = {}

        # Workspace buttons (1..4)
        for i in range(1, 5):
            btn = QPushButton(str(i))
            btn.setFixedSize(24, 24)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background-color: #888; border-radius: 8px; }
                QPushButton:hover { background-color: #00aaff; }
                QPushButton:checked { background-color: #00aaff; }
            """)
            btn.clicked.connect(lambda _, idx=i: self.switch_workspace(idx))
            self.topbar.addWidget(btn)
            self.workspace_buttons[i] = btn

        # Tiling mode buttons
        self.tiling_buttons = {
            "horizontal": QPushButton("H"),
            "vertical": QPushButton("V"),
            "bsp": QPushButton("B")
        }
        for mode, btn in self.tiling_buttons.items():
            btn.setFixedSize(24, 24)
            btn.setCheckable(True)
            btn.setProperty("class", "tilingBtn")  # so stylesheet applies
            btn.setObjectName(f"tilingBtn_{mode}")
            btn.clicked.connect(lambda _, m=mode: self.set_tiling_mode(m))
            self.topbar.addWidget(btn)

        self.topbar.addStretch()

        # # Profile icon
        # self.profile = QLabel()
        # self.profile.setPixmap(QPixmap(32, 32))
        # self.profile.setStyleSheet("border-radius: 16px; background-color: #555;")
        # self.profile.setFixedSize(32, 32)
        # self.topbar.addWidget(self.profile)

        # Window control buttons
        self.minimize_btn = QPushButton("−"); self.minimize_btn.setObjectName("minimizeBtn")
        self.minimize_btn.setFixedSize(24, 24); self.minimize_btn.clicked.connect(self.showMinimized); self.topbar.addWidget(self.minimize_btn)

        self.maximize_btn = QPushButton("□"); self.maximize_btn.setObjectName("maximizeBtn")
        self.maximize_btn.setFixedSize(24, 24); self.maximize_btn.clicked.connect(self.toggle_maximize); self.topbar.addWidget(self.maximize_btn)

        self.close_btn = QPushButton("×"); self.close_btn.setObjectName("closeBtn")
        self.close_btn.setFixedSize(24, 24); self.close_btn.clicked.connect(self.close); self.topbar.addWidget(self.close_btn)

        # Initialize workspaces (load or create)
        loaded = self._load_session()
        if loaded:
            # build from saved state
            for idx_str, ws_data in loaded.get("workspaces", {}).items():
                idx = int(idx_str)
                ws = Workspace()
                ws.load_from_dict(ws_data)
                self.workspaces[idx] = ws
            # Ensure we have 1..4 keys
            for i in range(1, 5):
                if i not in self.workspaces:
                    self.workspaces[i] = Workspace()
            start_idx = max(1, min(4, int(loaded.get("current_workspace_idx", 1))))
            self.switch_workspace(start_idx)
        else:
            for i in range(1, 5):
                self.workspaces[i] = Workspace()
            self.switch_workspace(1)

        # Floating Search Bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search or enter URL...")
        self.search_bar.setVisible(False)
        self.search_bar.returnPressed.connect(self.handle_search)

        # Keybinds
        self.shortcuts = {}
        keybinds = {
            "Ctrl+L": self.show_search_bar,
            "Ctrl+T": self.add_new_tab,
            "Ctrl+W": self.close_current_tab,
            "Ctrl+Shift+T": self.add_new_tile,
            "Ctrl+Tab": self.next_tab,
            "Ctrl+Shift+Tab": self.prev_tab,
            "Alt+Shift+Left": lambda: self.current_workspace.move_focus(-1) if self.current_workspace else None,
            "Alt+Shift+Right": lambda: self.current_workspace.move_focus(1) if self.current_workspace else None,
            "Alt+Left": self.go_back,
            "Alt+Right": self.go_forward,
            "Ctrl+Shift+H": lambda: self.set_tiling_mode("horizontal"),
            "Ctrl+Shift+V": lambda: self.set_tiling_mode("vertical"),
            "Ctrl+Shift+B": lambda: self.set_tiling_mode("bsp"),
            "Ctrl+Alt+Left": lambda: self.current_workspace.swap_tile(-1) if self.current_workspace else None,
            "Ctrl+Alt+Right": lambda: self.current_workspace.swap_tile(1) if self.current_workspace else None,
            "Ctrl+Alt+Up": lambda: self.current_workspace.resize_active_tile(30) if self.current_workspace else None,
            "Ctrl+Alt+Down": lambda: self.current_workspace.resize_active_tile(-30) if self.current_workspace else None,
            "Ctrl+Shift+Left":  lambda: self.current_workspace.move_tile("left")  if self.current_workspace else None,
            "Ctrl+Shift+Right": lambda: self.current_workspace.move_tile("right") if self.current_workspace else None,
            "Ctrl+Shift+Up":    lambda: self.current_workspace.move_tile("up")    if self.current_workspace else None,
            "Ctrl+Shift+Down":  lambda: self.current_workspace.move_tile("down")  if self.current_workspace else None,
        }
        for i in range(1, 5):
            keybinds[f"Ctrl+{i}"] = lambda idx=i: self.switch_workspace(idx)
        for key, callback in keybinds.items():
            sc = QShortcut(QKeySequence(key), self); sc.activated.connect(callback); self.shortcuts[key] = sc

    # ---------- Window + UI ----------
    def resizeEvent(self, event):
        self.center_search_bar()
        return super().resizeEvent(event)

    def toggle_maximize(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def center_search_bar(self, event=None):
        bar_width, bar_height = 400, 40
        x = (self.width() - bar_width) // 2
        y = self.height() // 5
        self.search_bar.setGeometry(x, y, bar_width, bar_height)
        if event:
            super().resizeEvent(event)

    def show_search_bar(self):
        self.search_bar.setVisible(True)
        self.center_search_bar()
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    # ---------- Tab/Tile actions ----------
    def add_new_tab(self):
        if self.current_workspace:
            ws_tile = self.current_workspace.active_tile()
            if not ws_tile:
                self.current_workspace.add_tile()
                ws_tile = self.current_workspace.active_tile()
            ws_tile.add_tab()

    def close_current_tab(self):
        if self.current_workspace:
            t = self.current_workspace.active_tile()
            if t and t.tabs.count() > 0:
                t.close_tab(t.tabs.currentIndex())
                # Clean up empty tiles and refresh
                self.current_workspace.update_tiles()

    def add_new_tile(self):
        if self.current_workspace:
            self.current_workspace.add_tile()

    def go_back(self):
        t = self.current_workspace.active_tile() if self.current_workspace else None
        if t: t.go_back()

    def go_forward(self):
        t = self.current_workspace.active_tile() if self.current_workspace else None
        if t: t.go_forward()

    def next_tab(self):
        t = self.current_workspace.active_tile() if self.current_workspace else None
        if t and t.tabs.count() > 0:
            t.tabs.setCurrentIndex((t.tabs.currentIndex() + 1) % t.tabs.count())

    def prev_tab(self):
        t = self.current_workspace.active_tile() if self.current_workspace else None
        if t and t.tabs.count() > 0:
            t.tabs.setCurrentIndex((t.tabs.currentIndex() - 1) % t.tabs.count())

    def move_tile_to_workspace(self, target_ws_index: int):
        """Move active tile to another workspace by index."""
        if not self.current_workspace:
            return

        tile = self.current_workspace.active_tile()
        if not tile:
            return

        # Prevent removing the very last tile
        if len(self.current_workspace.tiles) == 1:
            return

        detached = self.current_workspace.detach_tile(tile)
        if detached and 0 <= target_ws_index < len(self.workspaces):
            target_ws = self.workspaces[target_ws_index]
            target_ws.root_splitter.addWidget(detached)
            target_ws.update_tiles()


    # ---------- Mode + Workspace ----------
    def set_tiling_mode(self, mode):
        if self.current_workspace and mode in ["horizontal", "vertical", "bsp"]:
            self.current_workspace.set_tiling_mode(mode)
            for m, btn in self.tiling_buttons.items():
                btn.setChecked(m == mode)

    def switch_workspace(self, idx):
        if idx not in self.workspaces:
            return
        if self.current_workspace:
            self.workspace_area.removeWidget(self.current_workspace)
            self.current_workspace.setParent(None)
            self.workspace_buttons[self.current_workspace_idx].setChecked(False)
        self.current_workspace = self.workspaces[idx]
        self.current_workspace_idx = idx
        self.workspace_area.addWidget(self.current_workspace)
        self.current_workspace.update_tiles()
        self.workspace_buttons[idx].setChecked(True)
        for mode, btn in self.tiling_buttons.items():
            btn.setChecked(mode == self.current_workspace.tiling_mode)

    # ---------- Search ----------
    def handle_search(self):
        text = self.search_bar.text().strip()
        if not text:
            self.search_bar.setVisible(False)
            return

        if not self.current_workspace.tiles:
            self.current_workspace.add_tile()
        tile = self.current_workspace.active_tile()
        if not tile:
            self.current_workspace.add_tile()
            tile = self.current_workspace.active_tile()

        if " " not in text and ("." in text or text.startswith("http")):
            if not text.startswith("http"):
                text = "https://" + text
        else:
            text = f"https://www.google.com/search?q={text.replace(' ', '+')}"

        if tile.tabs.count() == 0:
            tile.add_tab(text)
        else:
            current_browser = tile.tabs.currentWidget()
            current_browser.setUrl(QUrl(text))

        QTimer.singleShot(100, lambda: self.search_bar.setVisible(False))

    # ---------- Session Persistence ----------
    def _save_session(self):
        data = {
            "current_workspace_idx": self.current_workspace_idx,
            "workspaces": {str(i): ws.to_dict() for i, ws in self.workspaces.items()}
        }
        try:
            with open(SESSION_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            # Log silently for now; keep MVP minimal
            print("Failed to save session:", e)

    def _load_session(self):
        if not os.path.exists(SESSION_PATH):
            return None
        try:
            with open(SESSION_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Failed to load session:", e)
            return None

    def closeEvent(self, event):
        self._save_session()
        return super().closeEvent(event)
