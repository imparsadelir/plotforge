from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from gui.style import apply_chart_style

apply_chart_style()


class PlotCanvas(FigureCanvasQTAgg):
    """A Matplotlib figure that behaves like a normal Qt widget."""

    def __init__(self):
        self.figure = Figure(figsize=(7, 4.5), dpi=100)
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)

    def reset(self, rows=1, cols=1):
        """Clear the figure and create a fresh grid of axes."""
        self.figure.clear()

        created = []
        for index in range(rows * cols):
            created.append(self.figure.add_subplot(rows, cols, index + 1))

        self.axes = created[0]
        return created