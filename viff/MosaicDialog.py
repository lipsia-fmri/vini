import sys, os.path
from .pyqtgraph_viff.Qt import QtCore, QtGui
import numpy as np
import math
import os
import time
import copy

from .pyqtgraph_viff import *
from .QxtSpanSliderH import QxtSpanSliderH

# testing input
from .testInputs import testFloat, testInteger


class MosaicDialog(QtGui.QDialog):
    """
    Mosaic dialog window
    """

    sigEdited = QtCore.Signal()
    sigFinished = QtCore.Signal()
    sigClosed = QtCore.Signal()

    def __init__(self):
        super(MosaicDialog, self).__init__()

        self.dims = [0,0,0]
        self.rows = 4
        self.cols = 4
        self.start = 0
        self.incr = 1
        self.plane = 't'

        # line regions
        self.lr_1 = None
        self.lr_2 = None

        self.layout = QtGui.QGridLayout()

        self.form_part = QtGui.QWidget()
        self.form = QtGui.QFormLayout()
        self.form_part.setLayout(self.form)
        self.slice_plane = QtGui.QComboBox()
        self.slice_plane.addItem("axial")
        self.slice_plane.addItem("sagittal")
        self.slice_plane.addItem("coronal")
        self.slice_plane.currentIndexChanged.connect(self.entriesEdited)
        # self.slice_plane.currentIndexChanged.connect(self.updatePlane)
        self.form.addRow("Choose slice plane:", self.slice_plane)

        # range slider
        self.slider_color = QtGui.QColor()
        self.slider_color.setRgb(255, 110, 0)
        self.slider_block = False
        self.range_sld = QxtSpanSliderH()
        self.range_sld.setRange(0, 255)
        self.range_sld.setSpan(0, 255)
        self.range_sld.setGradientLeftColor(self.slider_color)
        self.range_sld.setGradientRightColor(self.slider_color)
        self.range_sld.spanChanged.connect(self.setRangeFromSlider)
        self.form.addRow("Range:", self.range_sld)

        self.start_le = QtGui.QLineEdit("0")
        self.start_le.returnPressed.connect(self.entriesEdited)
        self.start_le.editingFinished.connect(self.entriesEdited)
        self.form.addRow("start:", self.start_le)

        self.end_le = QtGui.QLineEdit("")
        self.end_le.returnPressed.connect(self.entriesEdited)
        self.end_le.editingFinished.connect(self.entriesEdited)
        self.form.addRow("end:", self.end_le)

        self.rows_le = QtGui.QLineEdit("4")
        self.rows_le.returnPressed.connect(self.entriesEdited)
        self.rows_le.editingFinished.connect(self.entriesEdited)
        self.form.addRow("rows:", self.rows_le)

        self.cols_le = QtGui.QLineEdit("4")
        self.cols_le.returnPressed.connect(self.entriesEdited)
        self.cols_le.editingFinished.connect(self.entriesEdited)
        self.form.addRow("cols:", self.cols_le)

        self.increment_label = QtGui.QLabel("increment:")
        self.increment_label.setAlignment(
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)

        # close button
        self.close_button = QtGui.QPushButton('close', self)
        self.close_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.close_button.clicked.connect(self.closeEvent)
        self.close_button.setShortcut(QtGui.QKeySequence.Quit)

        # Slice Button
        self.slice_button = QtGui.QPushButton('Slice to mosaic!', self)
        self.slice_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slice_button.clicked.connect(self.slice)

        self.layout.addWidget(self.form_part, 0, 0, 6, 6)
        self.layout.addWidget(self.increment_label, 6, 0, 1, 6)
        self.layout.addWidget(self.slice_button, 7, 0, 1, 3)
        self.layout.addWidget(self.close_button, 7, 3, 1, 3)

        self.setLayout(self.layout)

    def reset(self):
        """
        Set the widgets to the correct values.
        """
        self.slice_plane.setCurrentIndex(0)
        self.rows_le.setText("4")
        self.cols_le.setText("4")
        self.start_le.setText("0")
        self.end_le.setText(str(int(self.dims[0]-1)))
        self.end = int(self.dims[0]-1)
        # Range slider update
        self.range_sld.setRange(0, self.end-1)
        self.range_sld.setSpan(0, self.end-1)
        self.incr = int(np.floor(self.dims[0]/16))

    def setDims(self, n_dims):
        """
        Updates the possible dimensions.
        """
        if self.dims[0] != n_dims[0] or self.dims[1] != n_dims[1] or self.dims[2] != n_dims[2]:
            self.dims = copy.copy(n_dims)
            self.reset()

    def closeEvent(self, ev=None):
        self.hide()
        self.sigClosed.emit()

    def slice(self):
        self.sigFinished.emit()

    def setRangeFromSlider(self):
        """
        Sets the values from the range to the line edits and calls for update.
        """
        self.slider_block = True
        # print(str(self.range_sld.lowerValue))
        # print(str(self.range_sld.upperValue))
        self.start = self.range_sld.lowerValue
        self.end = self.range_sld.upperValue
        self.start_le.setText(str(self.start))
        self.end_le.setText(str(self.end))
        self.entriesEdited()
        self.slider_block = False

    def entriesEdited(self):
        """
        Checks if entries are integers and emits signal to process data further.
        """
        if testInteger(self.rows_le.text()):
            self.rows = int(self.rows_le.text())
        else:
            return 0
        if testInteger(self.cols_le.text()):
            self.cols = int(self.cols_le.text())
        else:
            return 0
        if testInteger(self.start_le.text()):
            self.start = int(self.start_le.text())
            if self.start < 0:
                self.start = 0
                self.start_le.setText(str(int(self.start)))
        else:
            return 0
        if testInteger(self.end_le.text()):
            self.end = int(self.end_le.text())
        else:
            return 0
        if self.slice_plane.currentIndex() == 1:
            self.plane = 's'
            self.range_sld.setRange(0, self.dims[0]-1)
            if self.end >= self.dims[0]:
                self.end = self.dims[0]-1
                self.end_le.setText(str(int(self.end)))
            self.range_sld.setUpperPosition(self.end)
        if self.slice_plane.currentIndex() == 2:
            self.plane = 'c'
            self.range_sld.setRange(0, self.dims[1]-1)
            if self.end >= self.dims[1]:
                self.end = self.dims[1]-1
                self.end_le.setText(str(int(self.end)))
            self.range_sld.setUpperPosition(self.end)
        if self.slice_plane.currentIndex() == 0:
            self.plane = 't'
            self.range_sld.setRange(0, self.dims[2]-1)
            if self.end >= self.dims[2]:
                self.end = self.dims[2]-1
                self.end_le.setText(str(int(self.end)))
            self.range_sld.setUpperPosition(self.end)
        if not self.slider_block:
            self.range_sld.setSpan(self.start, self.end)
        self.sigEdited.emit()
