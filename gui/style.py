"""Visual theme for PlotForge: Qt stylesheet plus Matplotlib defaults."""

import matplotlib

# Okabe-Ito palette: distinguishable for the most common colour-vision
# deficiencies, which matters for printed academic figures.
CHART_COLORS = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#D55E00",
    "#CC79A7",
    "#56B4E9",
    "#8C6D31",
    "#333333",
]


PRESET_COLUMNS = 8

PRESET_COLORS = [
    # vivid
    "#E53935", "#FB8C00", "#FDD835", "#43A047",
    "#00ACC1", "#1E88E5", "#5E35B1", "#D81B60",
    # deep
    "#B71C1C", "#E65100", "#F9A825", "#1B5E20",
    "#006064", "#0D47A1", "#311B92", "#880E4F",
    # soft
    "#EF9A9A", "#FFCC80", "#FFF59D", "#A5D6A7",
    "#80DEEA", "#90CAF9", "#B39DDB", "#F48FB1",
    # neutral
    "#000000", "#424242", "#757575", "#9E9E9E",
    "#BDBDBD", "#D7CCC8", "#8D6E63", "#5D4037",
    # colour-blind safe (Okabe-Ito)
    "#0072B2", "#E69F00", "#009E73", "#D55E00",
    "#CC79A7", "#56B4E9", "#8C6D31", "#333333",
]

ACCENT = "#7C3AED"
ACCENT_HOVER = "#6D28D9"
ACCENT_SOFT = "#F2E9FE"
SECONDARY = "#FF6B4A"
SECONDARY_HOVER = "#EC5B3B"
BACKGROUND = "#F6F7FB"
SURFACE = "#FFFFFF"
BORDER = "#E4E5F0"
TEXT = "#1C1E2B"
MUTED = "#6E7391"

STYLESHEET = f"""
QWidget {{
    background: {BACKGROUND};
    color: {TEXT};
    font-size: 13px;
}}

QLabel#appTitle {{
    font-size: 19px;
    font-weight: 600;
    padding: 2px 0 0 0;
}}

QLabel#appSubtitle {{
    color: {MUTED};
    font-size: 12px;
    padding-bottom: 4px;
}}

QLabel#sectionLabel {{
    color: {MUTED};
    font-size: 11px;
    font-weight: 600;
    padding-top: 6px;
}}

QLabel#datasetName {{
    font-weight: 600;
}}

QLabel#emptyHint {{
    color: {MUTED};
    padding: 24px 8px;
}}

QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QFrame#chartFrame {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

QPushButton {{
    background: {SURFACE};
    border: 1px solid #D5DAE1;
    border-radius: 8px;
    padding: 7px 14px;
}}

QPushButton:hover {{
    background: {ACCENT_SOFT};
}}

QPushButton:pressed {{
    background: #E6D8FB;
}}

QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #9B5DF7, stop:1 {ACCENT});
    color: #FFFFFF;
    border: 1px solid {ACCENT};
    font-weight: 600;
}}

QPushButton#primary:hover {{
    background: {ACCENT_HOVER};
    border-color: {ACCENT_HOVER};
}}

QPushButton#secondary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FF8163, stop:1 {SECONDARY});
    color: #FFFFFF;
    border: 1px solid {SECONDARY};
    font-weight: 600;
}}

QPushButton#secondary:hover {{
    background: {SECONDARY_HOVER};
    border-color: {SECONDARY_HOVER};
}}

QPushButton#removeButton {{
    color: #B42318;
    border: none;
    background: transparent;
    padding: 2px 6px;
}}

QPushButton#removeButton:hover {{
    background: #FDECEA;
    border-radius: 6px;
}}

QLineEdit, QComboBox {{
    background: {SURFACE};
    border: 1px solid #D5DAE1;
    border-radius: 8px;
    padding: 6px 8px;
    selection-background-color: {ACCENT};
}}

QLineEdit:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}

QLineEdit:disabled {{
    background: #F1F3F5;
    color: #9AA3AD;
}}

QComboBox::drop-down {{
    border: none;
    width: 18px;
}}

QComboBox QAbstractItemView {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: #FFFFFF;
    outline: none;
}}

QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    background: {SURFACE};
    top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {MUTED};
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    color: {TEXT};
    font-weight: 600;
    border-bottom: 2px solid {ACCENT};
}}

QCheckBox {{
    spacing: 8px;
    padding: 2px 0;
}}

QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid #C6CDD5;
    background: {SURFACE};
}}

QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background: #C6CDD5;
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: #AAB3BC;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QSplitter::handle {{
    background: transparent;
    width: 8px;
}}

QToolBar {{
    border: none;
    background: {BACKGROUND};
    border-radius: 8px;
    padding: 3px;
    spacing: 3px;
}}

QToolBar QLabel {{
    background: transparent;
    color: {MUTED};
    font-size: 11px;
}}

QToolButton {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 5px;
    margin: 1px;
}}

QToolButton:hover {{
    background: {ACCENT_SOFT};
    border-color: {ACCENT};
}}

QToolButton:pressed, QToolButton:checked {{
    background: {ACCENT_SOFT};
    border-color: {ACCENT};
}}

QStatusBar {{
    color: {MUTED};
}}
"""


def apply_chart_style():
    """Set Matplotlib defaults so charts match the interface."""
    matplotlib.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": "#C6CDD5",
        "axes.labelcolor": TEXT,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "axes.titleweight": "600",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": matplotlib.cycler(color=CHART_COLORS),
        "grid.color": "#E7EAEE",
        "grid.linewidth": 0.9,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "text.color": TEXT,
        "legend.frameon": True,
        "legend.framealpha": 0.95,
        "legend.edgecolor": BORDER,
        "legend.fontsize": 9,
        "lines.linewidth": 1.8,
        "figure.autolayout": False,
    })


def light_palette():
    """A forced light palette.

    Matplotlib's navigation toolbar recolours its icons to white when it
    detects a dark palette. On systems with a dark system theme that makes
    the icons invisible against our light interface, so we pin the palette.
    """
    from PySide6.QtGui import QColor, QPalette

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BACKGROUND))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    return palette


def style_toolbar(toolbar, color=None, icon_size=20):
    """Repaint the Matplotlib toolbar icons in a colour we control.

    Matplotlib picks black or white icons based on the system palette,
    which can leave them invisible against our own background. Instead of
    guessing, we recolour every icon directly: the shape of the icon is
    kept and only its colour is replaced.
    """
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

    color = QColor(color or TEXT)
    size = QSize(icon_size, icon_size)
    toolbar.setIconSize(size)

    for action in toolbar.actions():
        icon = action.icon()
        if icon.isNull():
            continue

        pixmap = QPixmap(icon.pixmap(size))
        if pixmap.isNull():
            continue

        painter = QPainter(pixmap)
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn
        )
        painter.fillRect(pixmap.rect(), color)
        painter.end()

        action.setIcon(QIcon(pixmap))