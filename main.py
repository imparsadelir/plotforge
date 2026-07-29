import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlotForge — v0.0")
        self.resize(900, 600)

        self.canvas = PlotCanvas()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.canvas)
        self.setCentralWidget(container)

        self.draw_test_plot()

    def draw_test_plot(self):
        x = np.linspace(0, 10, 200)
        self.canvas.axes.plot(x, np.sin(x), label="sin(x)")
        self.canvas.axes.plot(x, np.cos(x), "--", label="cos(x)")
        self.canvas.axes.set_xlabel("x")
        self.canvas.axes.set_ylabel("y")
        self.canvas.axes.legend()
        self.canvas.axes.grid(alpha=0.3)
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    