from .pyqtgraph_vini.Qt import QtGui, QtCore
import numpy as np

from .pyqtgraph_vini import *


class TimePlot(GraphicsWindow):
    """
    Plots the time series of a voxel of a functional image.
    """

    def __init__(self, time_step = None, title="time plot"):
        super(TimePlot, self).__init__()

        self.resize(720,320)
        self.setWindowTitle('Time series')

        self.time = time_step

        # Linear region items' list for indicating experimental conditions.
        self.lri = []

        # Set the text and line color to black.
        setConfigOption('foreground', 'k')

        # Open a new plot with black pen.
        self.plot = self.addPlot(title="time plot: %s" %title, pen='k', labels={'left': "signal", 'bottom': "volumes"})
        self.curve = self.plot.plot(pen='k')
        self.setBackground('w')
        # Set configuration back to white for other widgets.
        setConfigOption('foreground', 'w')

        exit_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("window-close"), '&Exit', self)
        exit_action.setShortcut(QtGui.QKeySequence.Quit)
        exit_action.triggered.connect(self.closePlot)
        self.addAction(exit_action)

    def closePlot(self):
        self.hide()

    def setYRange(self, d_min, d_max):
        if (float('-inf') < float(d_min) < float('inf') and
                float('-inf') < float(d_max) < float('inf')):
            self.plot.setYRange(d_min, d_max)

    def setData(self, data, time):
        """
        Refresh the data.
        """
        self.time = time
        # TODO: only compute x once
        self.x = np.linspace(0.0, self.time*data.shape[0],
                             num=data.shape[0], endpoint=False)
        self.curve.setData(x=self.x, y=data)
        self.plot.autoRange()

    def delDesign(self):
        """
        If the design file is deleted the linear regions are removed here.
        """
        for i in self.lri:
            self.plot.removeItem(i)
        self.lri = []

    def setDesign(self, des_mat, colors):
        """
        Set new linear regions for the different experimental conditions.
        """
        # Remove old ones.
        for i in self.lri:
            self.plot.removeItem(i)
        # Create new ones.
        for i in range(0,des_mat.shape[0]):
            brush = mkBrush(colors[des_mat[i,0]])
            lr = LinearRegionItem(brush=brush, values=[des_mat[i,1],
                                     des_mat[i,1]+des_mat[i,2]])
            lr.setMovable(False)
            lr.setZValue(-10)
            self.lri.append(lr)

        # Add them to the plot.
        for i in self.lri:
            self.plot.addItem(i)
