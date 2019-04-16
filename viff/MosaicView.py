import sys
import os.path
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import math
import os
import time
import copy

import pyqtgraph as pg

import SliceBox
import MosaicSliceBox
# testing input
from testInputs import testFloat, testInteger


class MosaicView(QtGui.QWidget):
    """
    Mosaic View window
    """

    def __init__(self, rows, cols):
        super(MosaicView, self).__init__()

        self.resize(600,600)

        self.layout = QtGui.QGridLayout()

        self.rows = rows
        self.cols = cols
        self.number = rows*cols
        
        # GraphicsLayoutWidgets list
        self.glw = []
        self.viewboxes = []

        for i in range(self.rows):
            for j in range(self.cols):
                ind = i*self.cols+j
                # create new GraphicsLayoutWidget
                view_widget = pg.GraphicsLayoutWidget(self)
                view_widget.ci.layout.setContentsMargins(1, 1, 1, 1)
                view_widget.ci.layout.setSpacing(1)
                self.glw.append(view_widget)
                self.layout.addWidget(view_widget, i, j, 1, 1)
                # Puts a SliceBox (derived from ViewBox) in the Widget:
                view = MosaicSliceBox.MosaicSliceBox()
                view.useMyMenu(2)
                view.setAspectLocked(True)
                view_widget.addItem(view)
                # connect x and y ranges
                if len(self.viewboxes) != 0:
                    view.setXLink(self.viewboxes[0])
                    view.setYLink(self.viewboxes[0])
                self.viewboxes.append(view)

        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)

        self.zoom_in = QtGui.QAction('ZoomIn', self)
        self.zoom_in.setShortcut(QtGui.QKeySequence.ZoomIn)
        self.zoom_in.triggered.connect(self.zoomIn)
        self.addAction(self.zoom_in)

        self.zoom_out = QtGui.QAction('ZoomOut', self)
        self.zoom_out.setShortcut(QtGui.QKeySequence.ZoomOut)
        self.zoom_out.triggered.connect(self.zoomOut)
        self.addAction(self.zoom_out)

        self.reset_view = QtGui.QAction('reset view', self)
        self.reset_view.setShortcut(QtGui.QKeySequence('r'))
        self.reset_view.triggered.connect(self.autoRange)
        self.addAction(self.reset_view)

        self.exit_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("window-close"), '&Exit', self)
        self.exit_action.setShortcut(QtGui.QKeySequence.Quit)
        self.exit_action.triggered.connect(self.close)
        
        self.addAction(self.exit_action)

    def zoomIn(self):
        self.viewboxes[0].scaleBy(0.9)

    def zoomOut(self):
        self.viewboxes[0].scaleBy(1.1)

    def autoRange(self):
        self.viewboxes[0].autoRange()

    def resizeEvent(self, ev):
        self.autoRange()
        
