import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("低代码应用开发平台")
    app.setOrganizationName("LowCode")

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    app.setStyleSheet("""
        * {
            font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
