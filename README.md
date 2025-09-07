# Tyle Browser

## Overview
Tyle Browser is a cutting-edge, Chromium-based web browser designed to revolutionize multitasking with its integrated tiling window manager. Drawing inspiration from tiling window managers like i3wm and qtile, it delivers a sleek, minimalistic interface tailored for keyboard enthusiasts. This browser enables users to organize multiple web pages into a dynamic, customizable spatial workspace, boosting productivity and providing a seamless browsing experience.

## Features
- **Advanced Tiling System**: Supports horizontal, vertical, and BSP (Binary Space Partitioning) layouts for flexible window arrangements.
- **Keyboard-Centric Design**: Extensive keyboard shortcuts for efficient navigation and control.
- **Multi-Workspace Support**: Manage up to four distinct workspaces for organized browsing.
- **Tab and Tile Management**: Easily add, close, switch, and resize tabs and tiles.
- **Session Persistence**: Automatically saves and restores your browsing session on exit.
- **Modern Aesthetic**: Features a clean, customizable UI with a dark theme.


## Demo
[Watch the demo](misc/Tyle_recording.mp4)

## Installation

### Prerequisites
- Python 3.8 or later
- PySide6 (Qt for Python)
- PySide6.QtWebEngineWidgets (for Chromium integration)

Install dependencies via pip:
```bash
pip install -r requirements.txt
```

### Setup
1. Clone or download the repository to your local machine.
2. Launch the browser:
   ```bash
   python main.py
   ```

### Building a Standalone Executable (Optional)
For a desktop application with a custom taskbar icon:
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Create the executable:
   ```bash
   pyinstaller --onefile --windowed --icon=Tylelogo.ico main.py
   ```
4. Execute the generated file from the `dist` folder.

## Usage
- **Launch**: Start with `python main.py` or the built executable.
- **Workspaces**: Switch between workspaces 1-4 using the top bar buttons.
- **Tiling Modes**: Change layouts with H (horizontal), V (vertical), or B (BSP) buttons.
- **Search/URL**: Press Ctrl+L to activate the search bar, enter a URL or query, and press Enter.
- **Keyboard Shortcuts**:
  - **Ctrl+L**: Show search bar
  - **Ctrl+T**: Add new tab
  - **Ctrl+W**: Close current tab
  - **Ctrl+Shift+T**: Add new tile
  - **Ctrl+Tab**: Next tab
  - **Ctrl+Shift+Tab**: Previous tab
  - **Alt+Shift+Left/Right**: Move focus between tiles
  - **Alt+Left/Right**: Go back/forward in history
  - **Ctrl+Shift+H/V/B**: Switch to horizontal/vertical/BSP tiling mode
  - **Ctrl+Alt+Left/Right**: Swap active tile left/right
  - **Ctrl+Alt+Up/Down**: Resize active tile by 30 pixels
  - **Ctrl+Shift+Left/Right/Up/Down**: Move tile in the specified direction

## Files
- `main.py`: Application entry point and initialization.
- `TilingBrowser.py`: Core logic for the main window and workspace handling.
- `Tile.py`: Manages individual tiles with tab functionality.
- `Workspace.py`: Handles tiling layouts and tile interactions.

## Customization
  Use an absolute path or place the file in the project directory.
- **Styles**: Adjust the UI appearance by editing the `setStyleSheet` in `TilingBrowser.py`:
  ```python
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
  ```
  **KeyBinds**: Adjust the keybinds by editing keybinds variable in the `TilingBrowser.py`:
  ```python
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
  ```

## TODO
- Switch from Chromium to Gecko engine for alternative rendering.
- Implement lazy loading of tabs to improve performance.
- Add account integration for synchronized browsing data.

## Contributing
Contributions are welcome! Fork the repository, submit issues, or create pull requests to improve Tyle Browser.

## License
This project is open-source. Check the [LICENSE](LICENSE) file for details (if applicable).

## Contact
For support or inquiries, please use the project repository or relevant community channels.