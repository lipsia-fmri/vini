from pyqtgraph.Qt import QtGui, QtCore
import numpy as np

import pyqtgraph as pg


class HistogramThresholdWidget(pg.GraphicsWindow):

    sigChanged = QtCore.Signal()

    def __init__(self):

        super(HistogramThresholdWidget, self).__init__(title="Histogram")

        self.resize(750,375)

        # Set foreground black.
        pg.setConfigOption('foreground', 'k')

        self.plot = self.addPlot(title="Intensity Histogram")

        self.setBackground('w')
        pg.setConfigOption('foreground', 'w')

        # Set lower limit to 0 because histogram is positive.
        self.plot.setLimits(yMin = 0)

        color = QtGui.QColor()
        color.setRgb(0, 0, 170, 80)
        self.brush = pg.mkBrush(color)

        # Line regions
        self.lr_pos = None
        self.lr_neg = None

        exit_action = QtGui.QAction(QtGui.QIcon.fromTheme("window-close"), '&Exit', self)
        exit_action.setShortcut(QtGui.QKeySequence.Quit)
        exit_action.triggered.connect(self.closeHist)
        self.addAction(exit_action)

    def closeHist(self):
        self.hide()

    def setData(self, data):
        self.curve.setData(data)

    def setPlot(self, x, y):
        """
        Resets plot to given arrays.
        """
        self.plot.clear()
        self.plot.plot(x, y, pen='k')

    def LineRegionPos(self, low, high):
        """
        Initializes the line region tool for the positive color map.
        """
        if self.lr_pos is not None:
            self.plot.removeItem(self.lr_pos)
            self.lr_pos = None
        self.lr_pos = pg.LinearRegionItem(brush=self.brush, values=[low,high])
        self.lr_pos.setZValue(-1)
        self.plot.addItem(self.lr_pos)
        self.lr_pos.sigRegionChanged.connect(self.changed)
        self.lr_pos.sigRegionChangeFinished.connect(self.changed)

    def LineRegionNeg(self, low, high):
        """
        Initializes the line region tool for the negative color map.
        """
        if self.lr_neg is not None:
            self.plot.removeItem(self.lr_neg)
            self.lr_neg = None
        self.lr_neg = pg.LinearRegionItem(brush=self.brush, values=[low,high])
        self.lr_neg.setZValue(-1)
        self.plot.addItem(self.lr_neg)
        self.lr_neg.sigRegionChanged.connect(self.changed)
        self.lr_neg.sigRegionChangeFinished.connect(self.changed)

    def setPosRegion(self, low, high):
        """
        Resets the line region tool for the positive color map.
        """
        if self.lr_pos is not None:
            self.lr_pos.setRegion([low, high])

    def setNegRegion(self, low, high):
        """
        Resets the line region tool for the negative color map.
        """
        if self.lr_neg is not None:
            self.lr_neg.setRegion([low, high])

    def reset(self):
        """
        Deletes the line regions.
        """
        if self.lr_pos is not None:
            self.plot.removeItem(self.lr_pos)
            self.lr_pos = None
        if self.lr_neg is not None:
            self.plot.removeItem(self.lr_neg)
            self.lr_neg = None

    def setRange(self, ymax=0):
        self.plot.autoRange()
        if ymax != 0:
            self.plot.setYRange(0, ymax)

    def changed(self):
        self.sigChanged.emit()

    def getThresholdsPos(self):
        if self.lr_pos is not None:
            return self.lr_pos.getRegion()

    def getThresholdsNeg(self):
        if self.lr_neg is not None:
            return self.lr_neg.getRegion()
