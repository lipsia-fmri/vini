from pyqtgraph.Qt import QtGui, QtCore
import numpy as np

import pyqtgraph as pg


class HistogramThresholdWidget(pg.GraphicsWindow):

    sigChanged = QtCore.Signal()

    def __init__(self, pos=(150,150,600,600), title="Histogram"):

        super(HistogramThresholdWidget, self).__init__(title="Histogram")

        self.resize(750,375)
        self.setGeometry(pos[0], pos[1], pos[2], pos[3])

        # Set foreground black.
        pg.setConfigOption('foreground', 'k')

        self.plot = self.addPlot(title="Histogram: {}".format(title))

        self.setBackground('w')
        pg.setConfigOption('foreground', 'w')

        # Set lower limit to 0 because histogram is positive.
        self.plot.setLimits(yMin = 0)

        color = QtGui.QColor()
        color.setRgb(0, 0, 170, 40)
        self.brush = pg.mkBrush(color)

        # Line regions
        self.lr_pos = None
        self.lr_neg = None

        exit_action = QtGui.QAction(QtGui.QIcon.fromTheme("window-close"), '&Exit', self)
        exit_action.setShortcut(QtGui.QKeySequence.Quit)
        exit_action.triggered.connect(self.closeHist)
        self.addAction(exit_action)
        
        xax = self.plot.getAxis('bottom')
        
        # xax.maxTickLength = -10
        # xax.showValues = False
        # xax.setTickSpacing(100,20)

    def setTitle(self, title):
        self.plot.setTitle("Histogram: {}".format(title), color="#000000")


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
        self.lr_pos.setMovable(False)
        
        self.plot.addItem(self.lr_pos)

    def LineRegionNeg(self, low, high):
        """
        Initializes the line region tool for the negative color map.
        """
        if self.lr_neg is not None:
            self.plot.removeItem(self.lr_neg)
            self.lr_neg = None
        self.lr_neg = pg.LinearRegionItem(brush=self.brush, values=[low,high])
        self.lr_neg.setZValue(-1)
        self.lr_neg.setMovable(False)
        self.plot.addItem(self.lr_neg)

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



    def getThresholdsPos(self):
        if self.lr_pos is not None:
            return self.lr_pos.getRegion()

    def getThresholdsNeg(self):
        if self.lr_neg is not None:
            return self.lr_neg.getRegion()
