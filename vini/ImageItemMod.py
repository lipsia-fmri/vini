from .pyqtgraph_vini.Qt import QtCore, QtGui
import numpy as np
import sys
import weakref

from .pyqtgraph_vini import *
from .pyqtgraph_vini import functions as fn
from .pyqtgraph_vini import Point
from .pyqtgraph_vini import ItemGroup


class ImageItemMod(ImageItem):
    """
    Derived from a pyqtgraph class to make panning by dragging possible.
    """

    sigMouseDrag = QtCore.Signal(object)

    def __init__(self, image=None, **kargs):
        super(ImageItemMod, self).__init__()
        """
        See :func:`setImage <pyqtgraph.ImageItem.setImage>` for all allowed initialization arguments.
        """
        GraphicsObject.__init__(self)

    def mouseDragEvent(self, ev):
        ev.accept()

        self.sigMouseDrag.emit(ev)
        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return
        elif self.drawKernel is not None:
            ev.accept()
            self.drawAt(ev.pos(), ev)
