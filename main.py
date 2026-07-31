import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.style import STYLESHEET, light_palette


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("PlotForge")
    app.setPalette(light_palette())
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()