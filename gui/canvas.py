from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class PlotCanvas(FigureCanvasQTAgg):
    """A Matplotlib figure that behaves like a normal Qt widget."""

    def __init__(self):
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)

    def reset(self, rows=1, cols=1):
        """Clear the figure and create a fresh grid of axes.

        Returns the list of created axes. The first one is also stored
        as self.axes so the rest of the application keeps working.
        """
        self.figure.clear()

        created = []
        for index in range(rows * cols):
            created.append(self.figure.add_subplot(rows, cols, index + 1))

        self.axes = created[0]
        return created