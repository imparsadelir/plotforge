import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget , QFileDialog , QPushButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from core.io.readers import read_data_file

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
        self.setCentralWidget(container)
        
        button = QPushButton("open File")
        button.clicked.connect(self.open_file)
        layout.addWidget(self.canvas)
        layout.addWidget(button)
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            "",
            "Data Files (*.xlsx *.xls *.csv)"
        )

        if not file_path:
            return

        df = read_data_file(file_path)

        self.canvas.axes.clear()

        columns = list(df.columns)
        x_column = columns[0]
        y_columns = columns[1:]

        for col in y_columns:
            self.canvas.axes.plot(df[x_column], df[col], label=col)

        self.canvas.axes.set_xlabel(x_column)
        self.canvas.axes.legend()
        self.canvas.axes.grid(alpha=0.9)
        self.canvas.draw()
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    
    