"""Small custom widgets used by the PlotForge interface."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QColorDialog,
    QGridLayout,
    QMenu,
    QPushButton,
    QWidget,
    QWidgetAction,
)

from gui.style import PRESET_COLORS, PRESET_COLUMNS

AUTO_STYLE = (
    "border: 1px solid #C6CDD5; border-radius: 6px;"
    "background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
    " stop:0 #E53935, stop:0.25 #FDD835, stop:0.5 #43A047,"
    " stop:0.75 #1E88E5, stop:1 #8E24AA);"
)


class ColorButton(QPushButton):
    """A swatch that opens a palette of colours for one curve.

    Emits colorChanged with a hex string, or with None when the user
    asks for the automatic colour.
    """

    colorChanged = Signal(object)

    def __init__(self, color=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 24)
        self.setCursor(self.cursor())
        self._color = color
        self.clicked.connect(self.open_menu)
        self.refresh()

    def color(self):
        return self._color

    def set_color(self, color):
        self._color = color
        self.refresh()

    def refresh(self):
        """Repaint the swatch to match the current choice."""
        if self._color:
            self.setStyleSheet(
                f"background: {self._color};"
                "border: 1px solid #C6CDD5; border-radius: 6px;"
            )
            self.setToolTip(f"Colour: {self._color}")
        else:
            self.setStyleSheet(AUTO_STYLE)
            self.setToolTip("Automatic colour — click to choose your own")

    def choose(self, color, menu):
        menu.close()
        self.set_color(color)
        self.colorChanged.emit(color)

    def pick_custom(self, menu):
        menu.close()
        initial = self._color or "#1E88E5"
        chosen = QColorDialog.getColor(
            QColorDialog().currentColor(), self, "Choose a curve colour"
        )
        if chosen.isValid():
            self.set_color(chosen.name())
            self.colorChanged.emit(chosen.name())

    def open_menu(self):
        """Show a grid of presets plus the full colour dialog."""
        menu = QMenu(self)

        palette_widget = QWidget()
        grid = QGridLayout(palette_widget)
        grid.setContentsMargins(8, 8, 8, 4)
        grid.setSpacing(3)

        for index, color in enumerate(PRESET_COLORS):
            swatch = QPushButton()
            swatch.setFixedSize(20, 20)
            swatch.setToolTip(color)
            swatch.setStyleSheet(
                f"background: {color};"
                "border: 1px solid rgba(0, 0, 0, 0.18);"
                "border-radius: 4px;"
            )
            swatch.clicked.connect(
                lambda _checked=False, c=color, m=menu: self.choose(c, m)
            )
            grid.addWidget(
                swatch, index // PRESET_COLUMNS, index % PRESET_COLUMNS
            )

        holder = QWidgetAction(menu)
        holder.setDefaultWidget(palette_widget)
        menu.addAction(holder)
        menu.addSeparator()

        automatic = menu.addAction("Automatic colour")
        automatic.triggered.connect(
            lambda _checked=False, m=menu: self.choose(None, m)
        )

        more = menu.addAction("More colours…")
        more.triggered.connect(
            lambda _checked=False, m=menu: self.pick_custom(m)
        )

        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))