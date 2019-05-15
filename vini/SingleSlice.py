import sys
import os.path
from .pyqtgraph_vini.Qt import QtCore, QtGui
import numpy as np
import math
import os
import copy

from .pyqtgraph_vini import *

from .ColorMapWidget import *
from .SliceWidget import *
from .SliceBox import *
from .ImageItemMod import *


class SingleSlice(QtGui.QWidget):
    """
    Class to display a single slice (popout window).
    """

    def __init__(self, view):
        super(SingleSlice, self).__init__()

        # <ake it 400x400px large and place it in the center of the screen.
        self.resize(480,480)
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
                  (screen.height()-size.height())/2)

        self.l = QtGui.QGridLayout()
        self.setLayout(self.l)
        self.l.setContentsMargins(2,2,2,2)
        self.l.setSpacing(0)

        self.sw = SliceWidget(view)
        self.sw.useMenu(1)
        self.l.addWidget(self.sw)
        self.l.addWidget(self.sw, 0, 0, 10, 10)

        self.close_view = QtGui.QAction('close view', self)
        self.close_view.setShortcut(QtGui.QKeySequence.Quit)
        self.close_view.triggered.connect(self.close)
        self.addAction(self.close_view)

        self.reset_view = QtGui.QAction('reset view', self)
        self.reset_view.setShortcut(QtGui.QKeySequence('r'))
        self.reset_view.triggered.connect(self.sw.sb.autoRange)
        self.addAction(self.reset_view)

        self.zoom_in = QtGui.QAction('ZoomIn', self)
        self.zoom_in.setShortcut(QtGui.QKeySequence.ZoomIn)
        self.zoom_in.triggered.connect(self.sw.zoomIn)
        self.addAction(self.zoom_in)

        self.zoom_out = QtGui.QAction('ZoomOut', self)
        self.zoom_out.setShortcut(QtGui.QKeySequence.ZoomOut)
        self.zoom_out.triggered.connect(self.sw.zoomOut)
        self.addAction(self.zoom_out)

        if view == 'c':
            self.setWindowTitle("Coronal View")
        if view == 's':
            self.setWindowTitle("Sagittal View")
        if view == 't':
            self.setWindowTitle("Transverse View")
