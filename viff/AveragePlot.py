from pyqtgraph_viff.Qt import QtGui, QtCore
import copy

import pyqtgraph_viff as pg


class AveragePlot(pg.GraphicsWindow):
    """
    Plots the average of given experimental conditions over the trials at discrete time points.
    Updates with the move of the crosshair.
     """

    def __init__(self):
        super(AveragePlot, self).__init__()

        self.resize(720,320)
        self.setWindowTitle('conditional averages')

        # Dictionaries have condition numbers as keys and store the graph items.
        self.curves = {}
        self.uppers = {}
        self.lowers = {}
        self.fills = {}

        # Multiply standard error with this factor.
        self.c = 1

        # Set the text and line color to black.
        pg.setConfigOption('foreground', 'k')

        # Open a new plot with black pen.
        self.timeplot = self.addPlot(title="time averages")
        self.timeplot.addLegend(offset=(10, 10)) # args are (size, offset)
        self.setBackground('w')

        # Set configuration back to white for other widgets.
        pg.setConfigOption('foreground', 'w')

        exit_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("window-close"), '&Exit', self)
        exit_action.setShortcut(QtGui.QKeySequence.Quit)
        exit_action.triggered.connect(self.closePlot)
        self.addAction(exit_action)

    def closePlot(self):
        self.hide()

    def setCStddev(self, c):
        self.c = c

    def reset(self):
        """
        Deletes all plots and data.
        """
        self.curves = {}
        self.uppers = {}
        self.lowers = {}
        self.fills = {}
        self.timeplot.clear()
        self.timeplot.legend.items = []

    def updateData(self, cond, x, data, stderr, color):
        """
        For a condition number

        Arguments
        cond:
            experimental condition
        x:
            time points
        stderr:
            standard error of the data
        color:
            color of the experimental condition
        """
        if self.curves.has_key(cond):
            self.curves[cond].setData(x=x, y=data)
            self.uppers[cond].setData(x=x, y=data+self.c*stderr)
            self.lowers[cond].setData(x=x, y=data-self.c*stderr)
            self.timeplot.autoRange()
        else:
            pg.setConfigOption('foreground', 'k')
            curve = self.timeplot.plot(x=x, y=data, pen={'color': color, 'width': 3}, name="cond. " + str(cond))
            # light color for interior of the colored region
            color_light = copy.copy(color)
            color_light.setAlpha(int(color_light.alpha()/4.))
            # color for the border of the region
            color_a1 = copy.copy(color)
            color_a1.setAlpha(255)
            color_a1.setRgb(255, 255, 255)
            upper = self.timeplot.plot(
                x=x, y=data+self.c*stderr, pen={'color': color_a1, 'width': 1})
            lower = self.timeplot.plot(
                x=x, y=data-self.c*stderr, pen={'color': color_a1, 'width': 1})
            fill = pg.FillBetweenItem(lower, upper, color_light)
            self.timeplot.addItem(fill)
            pg.setConfigOption('foreground', 'w')
            self.curves[cond] = curve
            self.uppers[cond] = upper
            self.lowers[cond] = lower
            self.fills[cond] = fill
            self.timeplot.autoRange()
