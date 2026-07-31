import math
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QWidget,
    QFrame,
    QSplitter,
    QTabWidget,
    QFileDialog,
    QPushButton,
    QComboBox,
    QCheckBox,
    QLabel,
    QScrollArea,
    QLineEdit,
    QMessageBox,
    QMenu,
    QColorDialog,
    QWidgetAction,
)
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.ticker import MultipleLocator

from core.io.readers import read_data_file
from gui.canvas import PlotCanvas
from gui.style import style_toolbar

ALL_SELECTED = "All selected columns"

MODE_OVERLAY = "Overlay (all in one)"
MODE_PER_FILE = "One panel per file"
MODE_PER_COLUMN = "One panel per quantity"
MODES = [MODE_OVERLAY, MODE_PER_FILE, MODE_PER_COLUMN]

LEGEND_POSITIONS = [
    "Best",
    "Upper right",
    "Upper left",
    "Lower left",
    "Lower right",
    "Outside",
]

LINE_STYLES = {
    "Solid": "-",
    "Dashed": "--",
    "Dash-dot": "-.",
    "Dotted": ":",
}

PRESET_COLORS = [
    # colour-blind safe (Okabe-Ito)
    "#0072B2", "#E69F00", "#009E73", "#D55E00",
    "#CC79A7", "#56B4E9", "#8C6D31", "#333333",
    # vivid
    "#7C3AED", "#DB2777", "#E63946", "#F4A261",
    "#2A9D8F", "#0EA5E9", "#16A34A", "#EAB308",
    # deep
    "#1E3A8A", "#6B21A8", "#9D174D", "#B45309",
    "#0F766E", "#4D7C0F", "#475569", "#000000",
]


class ColorPicker(QPushButton):
    """A small swatch button for choosing the colour of one curve."""

    colorChanged = Signal(object)

    def __init__(self, color=None, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(30, 26)
        self.setMenu(self.build_menu())
        self.refresh()

    def color(self):
        return self._color

    def refresh(self):
        """Paint the button with the colour it represents."""
        shown = self._color or "#C9CDDB"
        self.setStyleSheet(
            f"QPushButton {{ background: {shown};"
            " border: 1px solid rgba(0, 0, 0, 0.18);"
            " border-radius: 7px; }"
            "QPushButton::menu-indicator { image: none; width: 0; }"
        )
        self.setToolTip(self._color or "Automatic colour")

    def choose(self, value):
        self._color = value
        self.refresh()
        self.colorChanged.emit(value)

    def pick_custom(self):
        start = QColor(self._color) if self._color else QColor("#7C3AED")
        chosen = QColorDialog.getColor(
            start,
            self,
            "Choose a curve colour",
            QColorDialog.ColorDialogOption.DontUseNativeDialog,
        )
        if chosen.isValid():
            self.choose(chosen.name())

    def build_menu(self):
        menu = QMenu(self)

        swatches = QWidget()
        grid = QGridLayout(swatches)
        grid.setContentsMargins(10, 10, 10, 6)
        grid.setSpacing(4)

        for index, value in enumerate(PRESET_COLORS):
            button = QPushButton()
            button.setFixedSize(22, 22)
            button.setToolTip(value)
            button.setStyleSheet(
                f"background: {value};"
                "border: 1px solid rgba(0, 0, 0, 0.15);"
                "border-radius: 5px;"
            )
            button.clicked.connect(
                lambda _checked=False, v=value, m=menu: (
                    self.choose(v), m.hide()
                )
            )
            grid.addWidget(button, index // 8, index % 8)

        holder = QWidgetAction(menu)
        holder.setDefaultWidget(swatches)
        menu.addAction(holder)
        menu.addSeparator()

        automatic = menu.addAction("Automatic colour")
        automatic.triggered.connect(lambda: self.choose(None))

        custom = menu.addAction("More colours…")
        custom.triggered.connect(self.pick_custom)

        return menu


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
    field.setMaximumWidth(80)
    return field


def section_label(text):
    """A small muted caption used above groups of controls."""
    label = QLabel(text.upper())
    label.setObjectName("sectionLabel")
    return label


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlotForge")
        self.resize(1280, 820)

        self.datasets = {}
        self.series_rows = []
        self.series_colors = {}

        self.canvas = PlotCanvas()
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setObjectName("chartToolbar")
        style_toolbar(self.toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.build_sidebar())
        splitter.addWidget(self.build_chart_area())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([380, 900])
        splitter.setChildrenCollapsible(False)

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 12, 12, 8)
        container_layout.addWidget(splitter)
        self.setCentralWidget(container)

        self.statusBar().showMessage("No data loaded — start by adding a file.")
        self.on_auto_range_changed()

    # ---------- interface construction ----------

    def build_sidebar(self):
        """The left-hand control panel."""
        title = QLabel("PlotForge")
        title.setObjectName("appTitle")

        subtitle = QLabel("Publication-quality charts from your data")
        subtitle.setObjectName("appSubtitle")
        subtitle.setWordWrap(True)

        add_button = QPushButton("Add files")
        add_button.setObjectName("primary")
        add_button.clicked.connect(self.open_files)

        clear_button = QPushButton("Clear all")
        clear_button.clicked.connect(self.clear_all)

        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(clear_button)

        tabs = QTabWidget()
        tabs.addTab(self.build_series_tab(), "Series")
        tabs.addTab(self.build_axes_tab(), "Axes")
        tabs.addTab(self.build_labels_tab(), "Labels")

        self.dpi_combo = QComboBox()
        self.dpi_combo.setEditable(True)
        self.dpi_combo.addItems(["72", "150", "300", "600", "1200"])
        self.dpi_combo.setCurrentText("300")
        self.dpi_combo.setMaximumWidth(90)

        save_button = QPushButton("Export chart")
        save_button.setObjectName("secondary")
        save_button.clicked.connect(self.save_chart)

        export_row = QHBoxLayout()
        export_row.addWidget(QLabel("DPI"))
        export_row.addWidget(self.dpi_combo)
        export_row.addStretch()
        export_row.addWidget(save_button)

        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(8)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(buttons)
        layout.addWidget(tabs, stretch=1)
        layout.addLayout(export_row)

        sidebar.setMinimumWidth(350)
        sidebar.setMaximumWidth(480)
        return sidebar

    def build_series_tab(self):
        """The list of loaded files and their columns."""
        self.series_container = QWidget()
        self.series_layout = QVBoxLayout(self.series_container)
        self.series_layout.setContentsMargins(4, 4, 4, 4)
        self.series_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidget(self.series_container)
        scroll.setWidgetResizable(True)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(scroll)

        self.rebuild_series_list()
        return page

    def build_axes_tab(self):
        """Column choice, layout mode, line style and axis ranges."""
        self.x_combo = QComboBox()
        self.x_combo.currentTextChanged.connect(self.on_x_changed)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(MODES)
        self.mode_combo.currentTextChanged.connect(self.plot_data)

        self.style_combo = QComboBox()
        self.style_combo.addItems(list(LINE_STYLES.keys()))
        self.style_combo.currentTextChanged.connect(self.plot_data)

        self.width_combo = QComboBox()
        self.width_combo.addItems(["1.0", "1.4", "1.8", "2.4", "3.0"])
        self.width_combo.setCurrentText("1.8")
        self.width_combo.currentTextChanged.connect(self.plot_data)

        line_row = QHBoxLayout()
        line_row.addWidget(self.style_combo, stretch=1)
        line_row.addWidget(self.width_combo)

        self.auto_range = QCheckBox("Fit the axes to the data automatically")
        self.auto_range.setChecked(True)
        self.auto_range.toggled.connect(self.on_auto_range_changed)

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

        ranges = QGridLayout()
        ranges.setHorizontalSpacing(6)
        ranges.addWidget(QLabel("X"), 0, 0)
        ranges.addWidget(self.x_min_edit, 0, 1)
        ranges.addWidget(self.x_max_edit, 0, 2)
        ranges.addWidget(self.x_step_edit, 0, 3)
        ranges.addWidget(QLabel("Y"), 1, 0)
        ranges.addWidget(self.y_min_edit, 1, 1)
        ranges.addWidget(self.y_max_edit, 1, 2)
        ranges.addWidget(self.y_step_edit, 1, 3)

        hint = QLabel(
            "Type a larger value in <b>min</b> than in <b>max</b> "
            "to reverse an axis."
        )
        hint.setObjectName("appSubtitle")
        hint.setWordWrap(True)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)
        layout.addWidget(section_label("Horizontal axis"))
        layout.addWidget(self.x_combo)
        layout.addWidget(section_label("Layout"))
        layout.addWidget(self.mode_combo)
        layout.addWidget(section_label("Line style and width"))
        layout.addLayout(line_row)
        layout.addWidget(section_label("Range"))
        layout.addWidget(self.auto_range)
        layout.addLayout(ranges)
        layout.addWidget(hint)
        layout.addStretch()
        return page

    def build_labels_tab(self):
        """Chart title, axis captions and legend options."""
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Chart title (optional)")

        self.x_label_edit = QLineEdit()
        self.x_label_edit.setPlaceholderText("Automatic")

        self.y_label_combo = QComboBox()
        self.y_label_combo.currentTextChanged.connect(self.plot_data)

        self.y_label_edit = QLineEdit()
        self.y_label_edit.setPlaceholderText(
            "Custom text (overrides the choice)"
        )

        for field in [self.title_edit, self.x_label_edit, self.y_label_edit]:
            field.editingFinished.connect(self.plot_data)

        self.legend_check = QCheckBox("Show legend")
        self.legend_check.setChecked(True)
        self.legend_check.toggled.connect(self.plot_data)

        self.legend_combo = QComboBox()
        self.legend_combo.addItems(LEGEND_POSITIONS)
        self.legend_combo.currentTextChanged.connect(self.plot_data)

        self.grid_check = QCheckBox("Show grid")
        self.grid_check.setChecked(True)
        self.grid_check.toggled.connect(self.plot_data)

        hint = QLabel(
            "Colour and legend text for each curve are set in the Series tab."
        )
        hint.setObjectName("appSubtitle")
        hint.setWordWrap(True)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)
        layout.addWidget(section_label("Title"))
        layout.addWidget(self.title_edit)
        layout.addWidget(section_label("Horizontal axis label"))
        layout.addWidget(self.x_label_edit)
        layout.addWidget(section_label("Vertical axis label"))
        layout.addWidget(self.y_label_combo)
        layout.addWidget(self.y_label_edit)
        layout.addWidget(section_label("Legend"))
        layout.addWidget(self.legend_check)
        layout.addWidget(self.legend_combo)
        layout.addWidget(section_label("Grid"))
        layout.addWidget(self.grid_check)
        layout.addWidget(hint)
        layout.addStretch()
        return page

    def build_chart_area(self):
        """The framed chart with its navigation toolbar."""
        frame = QFrame()
        frame.setObjectName("chartFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 6, 10, 10)
        layout.setSpacing(4)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=1)
        return frame

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
        for frame in self.datasets.values():
            for col in frame.columns:
                if col not in columns:
                    columns.append(col)
        return columns

    def open_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Open data files",
            "",
            "Data files (*.xlsx *.xls *.csv *.txt *.dat)"
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

            self.datasets[self.unique_name(Path(path).stem)] = frame

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
        self.series_colors.clear()
        self.refresh_controls()

    def remove_dataset(self, name):
        """Remove a single dataset and the colours that belong to it."""
        self.datasets.pop(name, None)
        for key in [k for k in self.series_colors if k[0] == name]:
            del self.series_colors[key]
        self.refresh_controls()

    def refresh_controls(self):
        """Rebuild the dropdowns and the series list after a data change."""
        columns = self.all_columns()

        previous_x = self.x_combo.currentText()
        self.x_combo.blockSignals(True)
        self.x_combo.clear()
        self.x_combo.addItems(columns)
        if previous_x in columns:
            self.x_combo.setCurrentText(previous_x)
        self.x_combo.blockSignals(False)

        self.refresh_label_options()
        self.rebuild_series_list()
        self.update_status()
        self.plot_data()

    def update_status(self):
        """Describe the loaded data in the status bar."""
        if not self.datasets:
            self.statusBar().showMessage(
                "No data loaded — start by adding a file."
            )
            return

        rows = sum(len(frame) for frame in self.datasets.values())
        files = len(self.datasets)
        noun = "file" if files == 1 else "files"
        self.statusBar().showMessage(f"{files} {noun} loaded — {rows:,} rows")

    # ---------- series list ----------

    def clear_series_list(self):
        """Remove every widget from the series panel."""
        while self.series_layout.count():
            item = self.series_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.series_rows.clear()

    def rebuild_series_list(self):
        """Build one card per dataset, with a row per column."""
        self.clear_series_list()

        if not self.datasets:
            hint = QLabel(
                "No files yet.\n\nUse “Add files” to load one or more "
                "spreadsheets or text files."
            )
            hint.setObjectName("emptyHint")
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint.setWordWrap(True)
            self.series_layout.addWidget(hint)
            self.series_layout.addStretch()
            return

        for name, frame in self.datasets.items():
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 10)
            card_layout.setSpacing(4)

            title = QLabel(name)
            title.setObjectName("datasetName")

            remove_button = QPushButton("Remove")
            remove_button.setObjectName("removeButton")
            remove_button.clicked.connect(
                lambda _checked=False, n=name: self.remove_dataset(n)
            )

            header = QHBoxLayout()
            header.addWidget(title)
            header.addStretch()
            header.addWidget(remove_button)
            card_layout.addLayout(header)

            for col in frame.columns:
                key = (name, col)

                picker = ColorPicker(self.series_colors.get(key))
                picker.colorChanged.connect(
                    lambda value, k=key: self.set_series_color(k, value)
                )

                checkbox = QCheckBox(str(col))
                checkbox.setChecked(True)
                checkbox.toggled.connect(self.plot_data)
                checkbox.setMinimumWidth(110)

                legend_edit = QLineEdit()
                legend_edit.setPlaceholderText("legend text")
                legend_edit.editingFinished.connect(self.plot_data)

                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(6)
                row_layout.addWidget(picker)
                row_layout.addWidget(checkbox)
                row_layout.addWidget(legend_edit, stretch=1)
                card_layout.addWidget(row)

                self.series_rows.append(
                    (row, checkbox, name, col, legend_edit, picker)
                )

            self.series_layout.addWidget(card)

        self.series_layout.addStretch()
        self.update_series_availability()

    def update_series_availability(self):
        """Hide the column that is currently used as the horizontal axis."""
        x_column = self.x_combo.currentText()
        for row, _checkbox, _name, col, _legend, _picker in self.series_rows:
            row.setVisible(col != x_column)

    def refresh_label_options(self):
        """Keep the Y-label choices in step with the horizontal axis."""
        x_column = self.x_combo.currentText()
        options = [ALL_SELECTED] + [
            col for col in self.all_columns() if col != x_column
        ]

        previous = self.y_label_combo.currentText()
        self.y_label_combo.blockSignals(True)
        self.y_label_combo.clear()
        self.y_label_combo.addItems(options)
        if previous in options:
            self.y_label_combo.setCurrentText(previous)
        self.y_label_combo.blockSignals(False)

    def on_x_changed(self):
        """React to a new horizontal axis choice."""
        self.update_series_availability()
        self.refresh_label_options()
        self.plot_data()

    def set_series_color(self, key, value):
        """Remember the colour chosen for one curve and redraw."""
        if value is None:
            self.series_colors.pop(key, None)
        else:
            self.series_colors[key] = value

        for _row, _checkbox, name, col, _legend, picker in self.series_rows:
            if (name, col) == key and picker.color() != value:
                picker.blockSignals(True)
                picker.choose(value)
                picker.blockSignals(False)

        self.plot_data()

    # ---------- plotting ----------

    def on_auto_range_changed(self):
        """Enable or disable the min/max fields based on auto mode."""
        enabled = not self.auto_range.isChecked()
        for field in self.limit_fields:
            field.setEnabled(enabled)
        self.plot_data()

    def selected_series(self, x_column):
        """Return the curves to draw as (dataset, column, label, colour)."""
        chosen = []
        for _row, checkbox, name, col, legend_edit, _picker in self.series_rows:
            if not checkbox.isChecked() or col == x_column:
                continue
            frame = self.datasets.get(name)
            if frame is None or x_column not in frame.columns:
                continue
            chosen.append((
                name,
                col,
                legend_edit.text().strip(),
                self.series_colors.get((name, col)),
            ))
        return chosen

    def group_series(self, series, mode):
        """Split the series into panels according to the chosen layout."""
        if mode == MODE_OVERLAY:
            return [("", series)]

        groups = {}
        for name, col, custom, color in series:
            key = name if mode == MODE_PER_FILE else col
            groups.setdefault(key, []).append((name, col, custom, color))

        return list(groups.items())

    def default_label(self, name, col, mode, single_panel):
        """Legend text used when the user has not typed one."""
        if single_panel or mode == MODE_OVERLAY:
            return f"{name} — {col}"
        if mode == MODE_PER_FILE:
            return str(col)
        return str(name)

    def build_y_label(self, plotted_names):
        """Decide what to write on the left-hand axis."""
        custom = self.y_label_edit.text().strip()
        if custom:
            return custom

        choice = self.y_label_combo.currentText()
        if choice and choice != ALL_SELECTED:
            return str(choice)

        return ", ".join(str(name) for name in plotted_names)

    def add_legend(self, axes):
        """Place the legend according to the chosen position."""
        if not self.legend_check.isChecked():
            return

        position = self.legend_combo.currentText()
        if position == "Outside":
            axes.legend(
                loc="center left",
                bbox_to_anchor=(1.02, 0.5),
                borderaxespad=0,
            )
        else:
            axes.legend(loc=position.lower())

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

    def draw_panel(self, axes, items, x_column, title, single_panel, mode):
        """Draw one panel of the chart."""
        plotted_names = []
        y_low = None
        y_high = None

        line_style = LINE_STYLES.get(self.style_combo.currentText(), "-")
        line_width = parse_number(self.width_combo.currentText()) or 1.8

        for name, col, custom, color in items:
            frame = self.datasets[name]
            values = frame[col]

            label = custom or self.default_label(name, col, mode, single_panel)
            axes.plot(
                frame[x_column],
                values,
                label=label,
                color=color,
                linestyle=line_style,
                linewidth=line_width,
            )

            if col not in plotted_names:
                plotted_names.append(col)

            low = values.min()
            high = values.max()
            y_low = low if y_low is None else min(y_low, low)
            y_high = high if y_high is None else max(y_high, high)

        axes.set_xlabel(self.x_label_edit.text().strip() or str(x_column))
        axes.set_ylabel(self.build_y_label(plotted_names))
        if self.grid_check.isChecked():
            axes.grid(True, alpha=0.7)
        else:
            axes.grid(False)

        if title:
            axes.set_title(str(title))

        if items:
            self.add_legend(axes)

        self.apply_axis_settings(axes, x_column, y_low, y_high)

    def show_empty_canvas(self, message):
        """Draw a friendly placeholder instead of an empty grid."""
        axes = self.canvas.reset(1, 1)[0]
        axes.set_axis_off()
        axes.text(
            0.5, 0.5, message,
            ha="center", va="center",
            fontsize=11, color="#9AA3AD",
            transform=axes.transAxes,
        )
        self.canvas.draw()

    def plot_data(self):
        if not self.datasets:
            self.show_empty_canvas("Add a data file to get started")
            return

        x_column = self.x_combo.currentText()
        if not x_column:
            self.show_empty_canvas("Choose a horizontal axis in the Axes tab")
            return

        mode = self.mode_combo.currentText()
        series = self.selected_series(x_column)

        if not series:
            self.show_empty_canvas(
                "Select at least one column in the Series tab"
            )
            return

        panels = self.group_series(series, mode)
        rows, cols = grid_for(len(panels))
        axes_list = self.canvas.reset(rows, cols)
        single_panel = len(panels) == 1

        for index, (title, items) in enumerate(panels):
            self.draw_panel(
                axes_list[index], items, x_column, title, single_panel, mode
            )

        for extra in axes_list[len(panels):]:
            extra.set_visible(False)

        figure = self.canvas.figure
        chart_title = self.title_edit.text().strip()

        if chart_title:
            figure.suptitle(chart_title, fontsize=13, fontweight="600")
            figure.tight_layout(rect=(0, 0, 1, 0.95))
        else:
            figure.tight_layout()

        self.canvas.draw()

    # ---------- export ----------

    def save_chart(self):
        """Save the current chart to an image or vector file."""
        if not self.datasets:
            QMessageBox.information(
                self, "Nothing to export", "Load a data file first."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export chart",
            "chart.png",
            "PNG image (*.png);;PDF document (*.pdf);;SVG vector (*.svg)"
        )

        if not file_path:
            return

        dpi = parse_number(self.dpi_combo.currentText())
        if dpi is None or dpi < 30:
            dpi = 300

        self.canvas.figure.savefig(
            file_path, dpi=int(dpi), bbox_inches="tight"
        )
        self.statusBar().showMessage(f"Saved to {file_path}", 5000)