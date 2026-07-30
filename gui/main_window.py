from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QPushButton,
    QComboBox,
)
from gui.canvas import PlotCanvas
from core.io.readers import read_data_file

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlotForge — v0.0")
        self.resize(900, 600)
        self.df = None
        self.x_combo = QComboBox()
        self.x_combo.currentTextChanged.connect(self.plot_data)
        
        

        self.canvas = PlotCanvas()

        container = QWidget()
        layout = QVBoxLayout(container)
        self.setCentralWidget(container)
        
        button = QPushButton("open File")
        button.clicked.connect(self.open_file)
        layout.addWidget(self.canvas)
        layout.addWidget(button)
        layout.addWidget(self.x_combo)
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            "",
            "Data Files (*.xlsx *.xls *.csv)"
        )

        if not file_path:
            return

        self.df = read_data_file(file_path)

        self.x_combo.clear()
        self.x_combo.addItems(list(self.df.columns))

        self.plot_data()

    def plot_data(self):
        if self.df is None or self.df.empty:
            return

        self.canvas.axes.clear()

        columns = list(self.df.columns)
        x_column = self.x_combo.currentText()
        y_columns = [c for c in columns if c != x_column]

        for col in y_columns:
            self.canvas.axes.plot(self.df[x_column], self.df[col], label=col)

        self.canvas.axes.set_xlabel(x_column)
        self.canvas.axes.legend()
        self.canvas.axes.grid(alpha=0.3)
        self.canvas.draw()