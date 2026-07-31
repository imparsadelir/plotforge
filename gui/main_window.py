import math
from pathlib import Path

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
    QLineEdit,
    QMessageBox,
)
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.ticker import MultipleLocator

from core.io.readers import read_data_file
from gui.canvas import PlotCanvas

ALL_SELECTED = "All selected columns"

MODE_OVERLAY = "Overlay (all in one)"
MODE_PER_FILE = "One panel per file"
MODE_PER_COLUMN = "One panel per quantity"
MODES = [MODE_OVERLAY, MODE_PER_FILE, MODE_PER_COLUMN]


def parse_number(text):
    """Convert text to a float. Return None if empty or invalid."""
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def format_tick(value):
    """Format an axis number without trailing zeros."""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4g}"


def mark_endpoints(axes, which):
    """Add the first and last value of the range as visible tick labels."""
    if which == "x":
        low, high = axes.get_xlim()
        current = axes.get_xticks()
    else:
        low, high = axes.get_ylim()
        current = axes.get_yticks()

    lower = min(low, high)
    upper = max(low, high)
    if upper <= lower:
        return

    gap = (upper - lower) * 0.06
    inner = [t for t in current if lower + gap < t < upper - gap]
    ticks = [lower] + list(inner) + [upper]
    labels = [format_tick(t) for t in ticks]

    if which == "x":
        axes.set_xticks(ticks)
        axes.set_xticklabels(labels)
    else:
        axes.set_yticks(ticks)
        axes.set_yticklabels(labels)


def grid_for(count):
    """Choose a pleasant rows x cols arrangement for a number of panels."""
    if count <= 1:
        return 1, 1
    if count == 2:
        return 1, 2
    if count <= 4:
        return 2, 2
    if count <= 6:
        return 2, 3
    return math.ceil(count / 3), 3


def make_number_field(placeholder):
    """Create a small text field for numeric input."""
    field = QLineEdit()
    field.setPlaceholderText(placeholder)
    field.setMaximumWidth(70)
    return field


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlotForge — v0.5")
        self.resize(1050, 800)

        self.datasets = {}
        self.y_checkboxes = []

        self.canvas = PlotCanvas()
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        open_button = QPushButton("Add Files")
        open_button.clicked.connect(self.open_files)

        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.clear_all)

        save_button = QPushButton("Save Chart")
        save_button.clicked.connect(self.save_chart)

        self.dpi_combo = QComboBox()
        self.dpi_combo.setEditable(True)
        self.dpi_combo.addItems(["72", "150", "300", "600", "1200"])
        self.dpi_combo.setCurrentText("300")
        self.dpi_combo.setMaximumWidth(90)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(MODES)
        self.mode_combo.currentTextChanged.connect(self.plot_data)

        self.x_combo = QComboBox()
        self.x_combo.currentTextChanged.connect(self.plot_data)

        # --- axis range controls ---
        self.x_min_edit = make_number_field("min")
        self.x_max_edit = make_number_field("max")
        self.x_step_edit = make_number_field("step")
        self.y_min_edit = make_number_field("min")
        self.y_max_edit = make_number_field("max")
        self.y_step_edit = make_number_field("step")

        self.limit_fields = [
            self.x_min_edit, self.x_max_edit,
            self.y_min_edit, self.y_max_edit,
        ]
        for field in self.limit_fields + [self.x_step_edit, self.y_step_edit]:
            field.editingFinished.connect(self.plot_data)

        self.auto_range = QCheckBox("Auto range")
        self.auto_range.setChecked(True)
        self.auto_range.stateChanged.connect(self.on_auto_range_changed)

        axis_row = QHBoxLayout()
        axis_row.addWidget(QLabel("X:"))
        axis_row.addWidget(self.x_min_edit)
        axis_row.addWidget(self.x_max_edit)
        axis_row.addWidget(QLabel("step"))
        axis_row.addWidget(self.x_step_edit)
        axis_row.addSpacing(25)
        axis_row.addWidget(QLabel("Y:"))
        axis_row.addWidget(self.y_min_edit)
        axis_row.addWidget(self.y_max_edit)
        axis_row.addWidget(QLabel("step"))
        axis_row.addWidget(self.y_step_edit)
        axis_row.addSpacing(25)
        axis_row.addWidget(self.auto_range)
        axis_row.addStretch()

        # --- axis labels ---
        self.x_label_edit = QLineEdit()
        self.x_label_edit.setPlaceholderText("X axis label (automatic)")
        self.y_label_edit = QLineEdit()
        self.y_label_edit.setPlaceholderText("Y axis label (overrides the choice)")

        for field in [self.x_label_edit, self.y_label_edit]:
            field.editingFinished.connect(self.plot_data)

        self.y_label_combo = QComboBox()
        self.y_label_combo.setMinimumWidth(150)
        self.y_label_combo.currentTextChanged.connect(self.plot_data)

        label_row = QHBoxLayout()
        label_row.addWidget(QLabel("X label:"))
        label_row.addWidget(self.x_label_edit)
        label_row.addWidget(QLabel("Y label:"))
        label_row.addWidget(self.y_label_combo)
        label_row.addWidget(self.y_label_edit)

        # --- checkbox area ---
        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidget(self.checkbox_container)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(130)
        scroll.setMaximumHeight(170)

        controls = QHBoxLayout()
        controls.addWidget(open_button)
        controls.addWidget(clear_button)
        controls.addWidget(save_button)
        controls.addWidget(QLabel("DPI:"))
        controls.addWidget(self.dpi_combo)
        controls.addWidget(QLabel("Layout:"))
        controls.addWidget(self.mode_combo)
        controls.addWidget(QLabel("X axis:"))
        controls.addWidget(self.x_combo)
        controls.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addLayout(axis_row)
        layout.addLayout(label_row)
        layout.addWidget(QLabel("Y columns:"))
        layout.addWidget(scroll)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.on_auto_range_changed()

    # ---------- data management ----------

    def unique_name(self, base):
        """Return a dataset name that is not already used."""
        name = base
        counter = 2
        while name in self.datasets:
            name = f"{base} ({counter})"
            counter += 1
        return name

    def all_columns(self):
        """Every column name across all datasets, without duplicates."""
        columns = []
        for df in self.datasets.values():
            for col in df.columns:
                if col not in columns:
                    columns.append(col)
        return columns

    def open_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Data Files",
            "",
            "Data Files (*.xlsx *.xls *.csv *.txt *.dat)"
        )

        if not file_paths:
            return

        failed = []
        for path in file_paths:
            try:
                frame = read_data_file(path)
            except Exception as error:
                failed.append(f"{Path(path).name}: {error}")
                continue

            name = self.unique_name(Path(path).stem)
            self.datasets[name] = frame

        self.refresh_controls()

        if failed:
            QMessageBox.warning(
                self,
                "Some files could not be opened",
                "\n\n".join(failed),
            )

    def clear_all(self):
        """Remove every loaded dataset."""
        self.datasets.clear()
        self.refresh_controls()

    def remove_dataset(self, name):
        """Remove a single dataset by name."""
        if name in self.datasets:
            del self.datasets[name]
        self.refresh_controls()

    def refresh_controls(self):
        """Rebuild the X dropdown, the label dropdown and the checkboxes."""
        columns = self.all_columns()

        previous_x = self.x_combo.currentText()
        self.x_combo.blockSignals(True)
        self.x_combo.clear()
        self.x_combo.addItems(columns)
        if previous_x in columns:
            self.x_combo.setCurrentText(previous_x)
        self.x_combo.blockSignals(False)

        previous_label = self.y_label_combo.currentText()
        options = [ALL_SELECTED] + columns
        self.y_label_combo.blockSignals(True)
        self.y_label_combo.clear()
        self.y_label_combo.addItems(options)
        if previous_label in options:
            self.y_label_combo.setCurrentText(previous_label)
        self.y_label_combo.blockSignals(False)

        self.build_checkboxes()
        self.plot_data()

    # ---------- checkboxes ----------

    def clear_checkboxes(self):
        """Remove all widgets from the checkbox area."""
        while self.checkbox_layout.count():
            item = self.checkbox_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.y_checkboxes.clear()

    def build_checkboxes(self):
        """Create a labelled group of checkboxes for each dataset."""
        self.clear_checkboxes()

        for name, df in self.datasets.items():
            header = QWidget()
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(0, 4, 0, 0)

            title = QLabel(f"<b>{name}</b>")
            remove_button = QPushButton("Remove")
            remove_button.setMaximumWidth(80)
            remove_button.clicked.connect(
                lambda _checked=False, n=name: self.remove_dataset(n)
            )

            header_layout.addWidget(title)
            header_layout.addStretch()
            header_layout.addWidget(remove_button)
            self.checkbox_layout.addWidget(header)

            for col in df.columns:
                checkbox = QCheckBox(f"    {col}")
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(self.plot_data)
                self.checkbox_layout.addWidget(checkbox)
                self.y_checkboxes.append((checkbox, name, col))

        self.checkbox_layout.addStretch()

    # ---------- plotting ----------

    def on_auto_range_changed(self):
        """Enable or disable the min/max fields based on auto mode."""
        enabled = not self.auto_range.isChecked()
        for field in self.limit_fields:
            field.setEnabled(enabled)
        self.plot_data()

    def selected_series(self, x_column):
        """Return the (dataset, column) pairs that should be drawn."""
        chosen = []
        for checkbox, name, col in self.y_checkboxes:
            if not checkbox.isChecked() or col == x_column:
                continue
            frame = self.datasets.get(name)
            if frame is None or x_column not in frame.columns:
                continue
            chosen.append((name, col))
        return chosen

    def group_series(self, series, mode):
        """Split the series into panels according to the chosen layout."""
        if mode == MODE_OVERLAY:
            return [("", series)]

        groups = {}
        for name, col in series:
            key = name if mode == MODE_PER_FILE else col
            groups.setdefault(key, []).append((name, col))

        return list(groups.items())

    def build_y_label(self, plotted_names):
        """Decide what to write on the left-hand axis."""
        custom = self.y_label_edit.text().strip()
        if custom:
            return custom

        choice = self.y_label_combo.currentText()
        if choice and choice != ALL_SELECTED:
            return str(choice)

        return ", ".join(str(name) for name in plotted_names)

    def apply_axis_settings(self, axes, x_column, y_low, y_high):
        """Apply limits, tick spacing and endpoint labels to one panel."""
        automatic = self.auto_range.isChecked()

        if automatic:
            lows = []
            highs = []
            for frame in self.datasets.values():
                if x_column in frame.columns:
                    lows.append(frame[x_column].min())
                    highs.append(frame[x_column].max())
            if lows:
                axes.set_xlim(min(lows), max(highs))

            if y_low is not None and y_high is not None and y_low != y_high:
                axes.set_ylim(y_low, y_high)
        else:
            axes.set_xlim(
                left=parse_number(self.x_min_edit.text()),
                right=parse_number(self.x_max_edit.text()),
            )
            axes.set_ylim(
                bottom=parse_number(self.y_min_edit.text()),
                top=parse_number(self.y_max_edit.text()),
            )

        x_step = parse_number(self.x_step_edit.text())
        if x_step is not None and x_step > 0:
            axes.xaxis.set_major_locator(MultipleLocator(x_step))
        elif automatic:
            mark_endpoints(axes, "x")

        y_step = parse_number(self.y_step_edit.text())
        if y_step is not None and y_step > 0:
            axes.yaxis.set_major_locator(MultipleLocator(y_step))
        elif automatic:
            mark_endpoints(axes, "y")

    def draw_panel(self, axes, items, x_column, title, single_panel):
        """Draw one panel and return the names that were plotted."""
        plotted_names = []
        y_low = None
        y_high = None

        for name, col in items:
            frame = self.datasets[name]
            values = frame[col]

            label = f"{name} — {col}" if single_panel else str(name)
            axes.plot(frame[x_column], values, label=label)

            if col not in plotted_names:
                plotted_names.append(col)

            low = values.min()
            high = values.max()
            y_low = low if y_low is None else min(y_low, low)
            y_high = high if y_high is None else max(y_high, high)

        axes.set_xlabel(self.x_label_edit.text().strip() or str(x_column))
        axes.set_ylabel(self.build_y_label(plotted_names))
        axes.grid(alpha=0.3)

        if title:
            axes.set_title(str(title), fontsize=10)

        if items:
            axes.legend(fontsize=8)

        self.apply_axis_settings(axes, x_column, y_low, y_high)
        return plotted_names

    def plot_data(self):
        figure = self.canvas.figure

        if not self.datasets:
            self.canvas.reset(1, 1)
            self.canvas.draw()
            return

        x_column = self.x_combo.currentText()
        if not x_column:
            self.canvas.reset(1, 1)
            self.canvas.draw()
            return

        mode = self.mode_combo.currentText()
        series = self.selected_series(x_column)
        panels = self.group_series(series, mode)

        if not panels or not series:
            self.canvas.reset(1, 1)
            self.canvas.draw()
            return

        rows, cols = grid_for(len(panels))
        axes_list = self.canvas.reset(rows, cols)
        single_panel = len(panels) == 1

        for index, (title, items) in enumerate(panels):
            self.draw_panel(
                axes_list[index], items, x_column, title, single_panel
            )

        # Hide any leftover empty panels in the grid.
        for extra in axes_list[len(panels):]:
            extra.set_visible(False)

        figure.tight_layout()
        self.canvas.draw()

    # ---------- export ----------

    def save_chart(self):
        """Save the current chart to an image or vector file."""
        if not self.datasets:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chart",
            "chart.png",
            "PNG Image (*.png);;PDF Document (*.pdf);;SVG Vector (*.svg)"
        )

        if not file_path:
            return

        dpi = parse_number(self.dpi_combo.currentText())
        if dpi is None or dpi < 30:
            dpi = 300

        self.canvas.figure.savefig(
            file_path,
            dpi=int(dpi),
            bbox_inches="tight"
        )