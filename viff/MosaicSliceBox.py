"""
This is needed for the MosaicView.
It is similar to the SliceBox but zooms to the cursor position.
"""

from .pyqtgraph_viff.Qt import QtCore, QtGui
import numpy as np
import sys

from .pyqtgraph_viff import *
from .pyqtgraph_viff import functions as fn
from .pyqtgraph_viff import Point
import weakref
from .pyqtgraph_viff import ItemGroup

class WeakList(object):

    def __init__(self):
        self._items = []

    def append(self, obj):
        #Add backwards to iterate backwards (to make iterating more efficient on removal).
        self._items.insert(0, weakref.ref(obj))

    def __iter__(self):
        i = len(self._items)-1
        while i >= 0:
            ref = self._items[i]
            d = ref()
            if d is None:
                del self._items[i]
            else:
                yield d
            i -= 1

class ChildGroup(ItemGroup):

    def __init__(self, parent):
        ItemGroup.__init__(self, parent)

        # Used as callback to inform ViewBox when items are added/removed from
        # the group.
        # Note 1: We would prefer to override itemChange directly on the
        #         ViewBox, but this causes crashes on PySide.
        # Note 2: We might also like to use a signal rather than this callback
        #         mechanism, but this causes a different PySide crash.
        self.itemsChangedListeners = WeakList()

        # excempt from telling view when transform changes
        self._GraphicsObject__inform_view_on_change = False

    def itemChange(self, change, value):
        ret = ItemGroup.itemChange(self, change, value)
        if change == self.ItemChildAddedChange or change == self.ItemChildRemovedChange:
            try:
                itemsChangedListeners = self.itemsChangedListeners
            except AttributeError:
                # It's possible that the attribute was already collected when the itemChange happened
                # (if it was triggered during the gc of the object).
                pass
            else:
                for listener in itemsChangedListeners:
                    listener.itemsChanged()
        return ret

class MosaicSliceBox(ViewBox):
    """
    **Bases:** :class:`GraphicsWidget <pyqtgraph.GraphicsWidget>`

    Box that allows internal scaling/panning of children by mouse drag.
    This class is usually created automatically as part of a :class:`PlotItem <pyqtgraph.PlotItem>` or :class:`Canvas <pyqtgraph.canvas.Canvas>` or with :func:`GraphicsLayout.addViewBox() <pyqtgraph.GraphicsLayout.addViewBox>`.

    Features:

    * Scaling contents by mouse or auto-scale when contents change
    * View linking--multiple views display the same data ranges
    * Configurable by context menu
    * Item coordinate mapping methods

    """

    sigYRangeChanged = QtCore.Signal(object, object)
    sigXRangeChanged = QtCore.Signal(object, object)
    sigRangeChangedManually = QtCore.Signal(object)
    sigRangeChanged = QtCore.Signal(object, object)
    #sigActionPositionChanged = QtCore.Signal(object)
    sigStateChanged = QtCore.Signal(object)
    sigTransformChanged = QtCore.Signal(object)
    sigResized = QtCore.Signal(object)

    center = [0, 0] # coordinates to zoom into.

    ## mouse modes
    PanMode = 3
    RectMode = 1

    ## axes
    XAxis = 0
    YAxis = 1
    XYAxes = 2

    ## for linking views together
    NamedViews = weakref.WeakValueDictionary()   # name: ViewBox
    AllViews = weakref.WeakKeyDictionary()       # ViewBox: None

    def __init__(self, parent=None, border=None, lockAspect=False, enableMouse=True, invertY=False, enableMenu=True, name=None, invertX=False):
        """
        ==============  =============================================================
        **Arguments:**
        *parent*        (QGraphicsWidget) Optional parent widget
        *border*        (QPen) Do draw a border around the view, give any
                        single argument accepted by :func:`mkPen <pyqtgraph.mkPen>`
        *lockAspect*    (False or float) The aspect ratio to lock the view
                        coorinates to. (or False to allow the ratio to change)
        *enableMouse*   (bool) Whether mouse can be used to scale/pan the view
        *invertY*       (bool) See :func:`invertY <pyqtgraph.ViewBox.invertY>`
        *invertX*       (bool) See :func:`invertX <pyqtgraph.ViewBox.invertX>`
        *enableMenu*    (bool) Whether to display a context menu when
                        right-clicking on the ViewBox background.
        *name*          (str) Used to register this ViewBox so that it appears
                        in the "Link axis" dropdown inside other ViewBox
                        context menus. This allows the user to manually link
                        the axes of any other view to this one.
        ==============  =============================================================
        """
        super(MosaicSliceBox, self).__init__(parent=None, border=border, lockAspect=True, enableMouse=True, invertY=False, enableMenu=True, name=None, invertX=False)
        self.zoomCenter = [0, 0]
        self.state['wheelScaleFactor'] = -0.025
        self.useMyMenu()

        """ linkedAxis saves to which axis of the linked view the axis is linked to """
        self.state['linkedAxis']= [None, None]

    def mouseDragEvent(self, ev, axis=None):
        ## if axis is specified, event will only affect that axis.
        ev.accept()  ## we accept all buttons
        pos = ev.pos()

        lastPos = ev.lastPos()
        dif = pos - lastPos
        dif = dif * -1

        ## Ignore axes if mouse is disabled
        mouseEnabled = np.array(self.state['mouseEnabled'], dtype=np.float)
        mask = mouseEnabled.copy()
        if axis is not None:
            mask[1-axis] = 0.0

        ## Scale or translate based on mouse button
        if ev.button() & (QtCore.Qt.RightButton | QtCore.Qt.MidButton):

            if self.state['mouseMode'] == MosaicSliceBox.RectMode:
                if ev.isFinish():  ## This is the final move in the drag; change the view scale now
                    #print "finish"
                    self.rbScaleBox.hide()
                    #ax = QtCore.QRectF(Point(self.pressPos), Point(self.mousePos))
                    ax = QtCore.QRectF(Point(ev.buttonDownPos(ev.button())), Point(pos))
                    ax = self.childGroup.mapRectFromParent(ax)
                    self.showAxRect(ax)
                    self.axHistoryPointer += 1
                    self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
                else:
                    ## update shape of scale box
                    self.updateScaleBox(ev.buttonDownPos(), ev.pos())

            else:
                tr = dif*mask
                tr = self.mapToView(tr) - self.mapToView(Point(0,0))
                x = tr.x() if mask[0] == 1 else None
                y = tr.y() if mask[1] == 1 else None

                self._resetTarget()
                if x is not None or y is not None:
                    self.translateBy(x=x, y=y)
                self.sigRangeChangedManually.emit(self.state['mouseEnabled'])
