from matplotlib import pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor


class MplCanvas(FigureCanvas):

    def __init__(self, parent, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.dataCursors = []
        self.axes: Axes = self.fig.add_subplot()
        self.line = 0
        self.cbar = 0
        self.fig.set_tight_layout(True)
        super().__init__(self.fig)
        self.navToolBar = NavigationToolbar(self, parent=parent)
        self.title = "Espectrograma"
        self.XAxisTitle = 'Tiempo [s]'
        self.YAxisTitle = 'Frecuencia [Hz]'
        self.XScale = 'linear'
        self.YScale = 'log'
        parent.layout().addWidget(self.navToolBar, 0, 0)
        parent.layout().addWidget(self, 1, 0, 1, 11)

        self.cursor = Cursor(self.axes, useblit=True,
                             color='gray', linestyle='--', linewidth=0.8)

    def changePlotTitle(self, title: str):
        self.title = title

    def changeXAxisTitle(self, title: str):
        self.XAxisTitle = title

    def changeYAxisTitle(self, title: str):
        self.YAxisTitle = title

    def plot(self, audio: np.ndarray, toffset=0):
        if self.cbar != 0:
            self.cbar.remove()
        self.axes.clear()

        def window(x): return x*np.bartlett(len(x))
        audio = audio + np.random.normal(0, 1e-10, len(audio))
        spectrum, f, t, self.line = self.axes.specgram(
            audio, Fs=44100, window=window, mode='magnitude', scale='dB')
        self.axes.xaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: str(x+toffset)))
        self.cbar = plt.colorbar(
            mappable=self.line, ax=self.axes, format="%i dB", )
        # self.axes.set_xscale(self.XScale)
        # self.axes.set_yscale(self.YScale)
        self.axes.set_title(
            self.title)
        self.axes.set_xlabel(
            self.XAxisTitle)
        self.axes.set_ylabel(
            self.YAxisTitle)

        # self.axes.set_ylim(top=f[-1], bottom=10)
        # self.axes.set_xlim(right=t[-1], left=t[0])

        self.fig.canvas.draw()
