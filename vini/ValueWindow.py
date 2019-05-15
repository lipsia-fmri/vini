from .pyqtgraph_vini.Qt import QtCore, QtGui
import numpy as np
import math
import os
import copy
import sys, os.path

from .pyqtgraph_vini  import *


class ValueWindow(QtGui.QWidget):
    """
    Displays cursor and crosshair intensity values and coordinates of all
    images.
    """

    def __init__(self):
        super(ValueWindow, self).__init__()

        self.resize(400,200)
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        # Place it in the center of the screen.
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

        self.l = QtGui.QGridLayout()
        self.setLayout(self.l)
        self.l.setSpacing(0)

        self.cross_values_lbl = QtGui.QLabel("<b>Values at the crosshair</b>")
        self.cross_values_lbl.setAlignment(
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.l.addWidget(self.cross_values_lbl, 0, 0, 1, 6)

        self.cross_names_lbl = QtGui.QLabel("")
        self.cross_values_lbl = QtGui.QLabel("")
        self.cross_coords_lbl = QtGui.QLabel("")
        self.l.addWidget(self.cross_names_lbl, 1, 0, 5, 2)
        self.l.addWidget(self.cross_values_lbl, 1, 2, 5, 2)
        self.l.addWidget(self.cross_coords_lbl, 1, 4, 5, 2)

        self.cursor_values_lbl = QtGui.QLabel("<b>Values at the cursor</b>")
        self.cursor_values_lbl.setAlignment(
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.l.addWidget(self.cursor_values_lbl, 6, 0, 1, 6)

        self.cursor_names_lbl = QtGui.QLabel("")
        self.cursor_values_lbl = QtGui.QLabel("")
        self.cursor_coords_lbl = QtGui.QLabel("")
        self.l.addWidget(self.cursor_names_lbl, 7, 0, 5, 2)
        self.l.addWidget(self.cursor_values_lbl, 7, 2, 5, 2)
        self.l.addWidget(self.cursor_coords_lbl, 7, 4, 5, 2)

        self.close_view = QtGui.QAction('close view', self)
        self.close_view.setShortcut(QtGui.QKeySequence.Quit)
        self.close_view.triggered.connect(self.close)
        self.addAction(self.close_view)

        self.setWindowTitle("Crosshair and Cursor values")

    def closeEvent(self, ev):
        self.hide()
