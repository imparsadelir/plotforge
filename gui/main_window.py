from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QPushButton,
    QComboBox,
    QCheckBox,
    QLabel,
    QScrollArea,
)

from core.io.readers import read_data_file
from gui.canvas import PlotCanvas


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlotForge — v0.1")
        self.resize(1000, 650)

        self.df = None
        self.y_checkboxes = []

        self.canvas = PlotCanvas()

        open_button = QPushButton("Open File")
        open_button.clicked.connect(self.open_file)
        
        save_button = QPushButton("Save Chart")
        save_button.clicked.connect(self.save_chart)

        self.x_combo = QComboBox()
        self.x_combo.currentTextChanged.connect(self.plot_data)

        # ناحیه‌ای که چک‌باکس‌ها داخلش ساخته می‌شوند
        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidget(self.checkbox_container)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(120)

        controls = QHBoxLayout()
        controls.addWidget(open_button)
        controls.addWidget(save_button)
        controls.addWidget(QLabel("X axis:"))
        controls.addWidget(self.x_combo)
        controls.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(QLabel("Y columns:"))
        layout.addWidget(scroll)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def clear_checkboxes(self):
        """Remove all existing Y-column checkboxes."""
        while self.checkbox_layout.count():
            item = self.checkbox_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.y_checkboxes.clear()

    def build_checkboxes(self, columns):
        """Create one checkbox per column."""
        self.clear_checkboxes()

        for col in columns:
            checkbox = QCheckBox(col)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.plot_data)
            self.checkbox_layout.addWidget(checkbox)
            self.y_checkboxes.append(checkbox)

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
        columns = list(self.df.columns)

        self.x_combo.clear()
        self.x_combo.addItems(columns)

        self.build_checkboxes(columns)

        self.plot_data()
        
    def save_chart(self):
        
        if self.df is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chart",
            "chart.png",
            "PNG Image (*.png);;PDF Document (*.pdf);;SVG Vector (*.svg)"
        )

        if not file_path:
            return

        self.canvas.figure.savefig(
            file_path,
            dpi=300,
            bbox_inches="tight"
        )

    def plot_data(self):
        if self.df is None or self.df.empty:
            return

        x_column = self.x_combo.currentText()
        if not x_column:
            return

        y_columns = [
            cb.text() for cb in self.y_checkboxes
            if cb.isChecked() and cb.text() != x_column
        ]

        self.canvas.axes.clear()

        for col in y_columns:
            self.canvas.axes.plot(self.df[x_column], self.df[col], label=col)

        self.canvas.axes.set_xlabel(x_column)
        self.canvas.axes.grid(alpha=0.3)

        if y_columns:
            self.canvas.axes.legend()

        self.canvas.draw()