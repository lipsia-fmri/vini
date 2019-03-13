from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import sys
import weakref

import pyqtgraph as pg
from pyqtgraph import functions as fn
from pyqtgraph import Point
from pyqtgraph import ItemGroup


class ImageItemMod(pg.ImageItem):
    """
    Derived from a pyqtgraph class to make panning by dragging possible.
    """

    sigMouseDrag = QtCore.Signal(object)

    def __init__(self, image=None, **kargs):
        super(ImageItemMod, self).__init__()
        """
        See :func:`setImage <pyqtgraph.ImageItem.setImage>` for all allowed initialization arguments.
        """
        pg.GraphicsObject.__init__(self)

    def mouseDragEvent(self, ev):
        ev.accept()

        self.sigMouseDrag.emit(ev)
        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return
        elif self.drawKernel is not None:
            ev.accept()
            self.drawAt(ev.pos(), ev)
