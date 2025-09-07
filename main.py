from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon  
import sys
import TilingBrowser


def main():
    app = QApplication(sys.argv)
    try:
        app.setWindowIcon(QIcon(r"misc\Tylelogo.ico"))
    except Exception as e:
        print(e)
    win = TilingBrowser.TilingBrowser()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()