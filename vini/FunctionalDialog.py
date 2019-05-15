from .pyqtgraph_vini.Qt import QtCore, QtGui
import numpy as np
import math
import os
import time
import copy
import sys, os.path

from .pyqtgraph_vini import *

from .testInputs import testFloat, testInteger


class FunctionalDialog(QtGui.QDialog):
    """
    Functional image properties dialog
    """

    # Emits when something is changed.
    sigChanged = QtCore.Signal()
    # Emits when new design file is loaded.
    sigDesignFile = QtCore.Signal(str)
    # Emits when design file has to be removed.
    sigDelDesMat = QtCore.Signal()
    # Emits when trial averages are to be computed.
    sigComputeTA = QtCore.Signal()

    def __init__(self):
        super(FunctionalDialog, self).__init__()

        # TR
        self.frame_time = 1.0
        # Design file file name
        self.fname = ""

        # condition averages
        # variables for delta x, condition length and list of conditions
        self.cond_dx = None
        self.cond_time = None
        self.cond_conds = []
        # Number of standard errors for plot.
        self.cond_stddevs = 2.0

        self.layout = QtGui.QGridLayout()
        self.resize(320,320)

        self.qtab = QtGui.QTabWidget()
        self.tab1 = QtGui.QWidget()
        self.tab2 = QtGui.QWidget()

        # First tab: TR and design file
        self.form1 = QtGui.QFormLayout()
        self.tab1.setLayout(self.form1)

        self.frame_le = QtGui.QLineEdit()
        self.frame_le.setMaxLength(5)
        self.frame_le.returnPressed.connect(self.savePreferences)
        self.frame_le.editingFinished.connect(self.savePreferences)
        self.form1.addRow("TR in sec:", self.frame_le)
        self.design_button = QtGui.QPushButton("Load")
        self.design_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.design_button.clicked.connect(self.openDesignFile)
        self.form1.addRow("Load design file", self.design_button)
        self.del_design_button = QtGui.QPushButton("Remove")
        self.del_design_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.del_design_button.clicked.connect(self.delDesignFile)
        self.form1.addRow("Remove design file", self.del_design_button)

        # Second tab: trial averages for experimental conditions
        self.form2 = QtGui.QFormLayout()
        self.tab2.setLayout(self.form2)
        self.deltax_le = QtGui.QLineEdit()
        self.form2.addRow("Time sampling [sec]:", self.deltax_le)
        self.time_le = QtGui.QLineEdit()
        self.form2.addRow("Length [sec]:", self.time_le)
        self.cond_le = QtGui.QLineEdit()
        self.form2.addRow("Conditions:", self.cond_le)
        self.stddevs_le = QtGui.QLineEdit()
        self.form2.addRow("Plot +-c*stderr, c=", self.stddevs_le)

        self.compute_button = QtGui.QPushButton("Compute averages", self)
        self.compute_button.setFocusPolicy(QtCore.Qt.NoFocus)
        self.compute_button.clicked.connect(self.computeTA)
        self.form2.addRow("Trial Averages:", self.compute_button)

        self.quit = QtGui.QAction('Quit', self)
        self.quit.setShortcut(QtGui.QKeySequence.Quit)
        self.quit.triggered.connect(self.closeDialog)
        self.addAction(self.quit)

        self.qtab.addTab(self.tab1, "General")
        self.qtab.addTab(self.tab2, "Trial Averages")

        self.layout.addWidget(self.qtab, 0, 0, 6, 6)

        self.setLayout(self.layout)

    def setPreferences(self, **kwargs):
        """
        Reset the entries to the passed arguments.
        """
        self.frame_time = kwargs['frame_time']
        self.frame_le.setText(str(self.frame_time))
        self.deltax_le.setText(str(self.frame_time))
        self.stddevs_le.setText(str(self.cond_stddevs))
        if kwargs.has_key('length'):
            self.cond_time = kwargs['length']
            self.time_le.setText(str(self.cond_time))
        if kwargs.has_key('conds'):
            conds = kwargs['conds']
            self.cond_le.setText(" ".join([str(i) for i in kwargs['conds']]))

    def setAverageSettings(self, length, conds):
        """
        Resets trial average settings.
        """
        self.cond_time = length
        self.time_le.setText(str(self.cond_time))
        self.cond_le.setText(" ".join([str(i) for i in conds]))
        self.stddevs_le.setText(str(self.cond_stddevs))

    def savePreferences(self):
        if testFloat(self.frame_le.text()):
            self.frame_time = float(self.frame_le.text())
        self.sigChanged.emit()

    def openDesignFile(self):
        """
        Lets design file to be chosen and emits signal.
        """
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file')
        self.sigDesignFile.emit(fname)

    def delDesignFile(self):
        self.sigDelDesMat.emit()

    def getFrameTime(self):
        return self.frame_time

    def computeTA(self):
        """
        Checks input for trial averages and emits signal.
        """
        # read in boxes and emit signal to trigger the average time plot
        if testFloat(self.deltax_le.text()):
            if float(self.deltax_le.text()) > 1000:
                QtGui.QMessageBox.warning(self, "Warning",
                    "Keep in mind that the time sampling is given in seconds.")
            self.cond_dx = float(self.deltax_le.text())
        else:
            QtGui.QMessageBox.warning(self, "Warning",
                "Time sampling could not be interpreted as a float.")
            return 0
        if testFloat(self.time_le.text()):
            self.cond_time = float(self.time_le.text())
        else:
            QtGui.QMessageBox.warning(self, "Warning",
                "Time could not be interpreted as a float.")
            return 0
        if testFloat(self.stddevs_le.text()):
            self.cond_stddevs = float(self.stddevs_le.text())
        else:
            QtGui.QMessageBox.warning(self, "Warning",
                "Input could not be interpreted as a float.")
            return 0
        cond_text = self.cond_le.text()
        conditions = cond_text.split()
        self.cond_conds = []
        for cond in conditions:
            if testInteger(cond):
                self.cond_conds.append(int(cond))
            else:
                QtGui.QMessageBox.warning(self, "Warning",
                    "Could not interpret condition index.")
        self.sigComputeTA.emit()

    def closeDialog(self):
        self.close()
