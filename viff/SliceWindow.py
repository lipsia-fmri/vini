from pyqtgraph_viff.Qt import QtCore, QtGui
import numpy as np
import math
import os
import copy
import sys, os.path

import pyqtgraph_viff  as pg

import ColorMapWidget
import SliceWidget
import SliceBox
import ImageItemMod


class SliceWindow(QtGui.QWidget):
    """
    Class to display an extra window.
    """

    sigClose = QtCore.Signal(int)

    def __init__(self, window_number):
        super(SliceWindow, self).__init__()

        self.resize(960,320)
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.id = window_number
        # Place it in the center of the screen.
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

        self.l = QtGui.QGridLayout()
        self.setLayout(self.l)
        self.l.setContentsMargins(2,2,2,2)
        self.l.setSpacing(0)

        self.sw_c = SliceWidget.SliceWidget('c')
        self.sw_s = SliceWidget.SliceWidget('s')
        self.sw_t = SliceWidget.SliceWidget('t')
        self.sw_c.useMenu(1)
        self.sw_s.useMenu(1)
        self.sw_t.useMenu(1)
        self.l.addWidget(self.sw_c)
        self.l.addWidget(self.sw_c, 0, 0, 12, 12)
        self.l.addWidget(self.sw_s)
        self.l.addWidget(self.sw_s, 0, 12, 12, 12)
        self.l.addWidget(self.sw_t)
        self.l.addWidget(self.sw_t, 0, 24, 12, 12)

        self.close_view = QtGui.QAction('close view', self)
        self.close_view.setShortcut(QtGui.QKeySequence.Quit)
        self.close_view.triggered.connect(self.close)
        self.addAction(self.close_view)

        # self.reset_view = QtGui.QAction('reset view', self)
        # self.reset_view.setShortcut(QtGui.QKeySequence('r'))
        # self.addAction(self.reset_view)

        # self.zoom_in = QtGui.QAction('ZoomIn', self)
        # self.zoom_in.setShortcut(QtGui.QKeySequence.ZoomIn)
        # # self.zoom_in.triggered.connect(self.sw.zoomIn)
        # self.addAction(self.zoom_in)

        # self.zoom_out = QtGui.QAction('ZoomOut', self)
        # self.zoom_out.setShortcut(QtGui.QKeySequence.ZoomOut)
        # # self.zoom_out.triggered.connect(self.sw.zoomOut)
        # self.addAction(self.zoom_out)

        self.setWindowTitle("Window " + str(window_number))

        self.show()

    def closeEvent(self, ev):
        self.sigClose.emit(self.id)
        self.hide()
