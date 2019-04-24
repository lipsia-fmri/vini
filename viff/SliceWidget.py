from .pyqtgraph_viff.Qt import QtCore, QtGui
import sys
import numpy as np
import weakref

from .pyqtgraph_viff import *
from .pyqtgraph_viff import functions as fn
from .pyqtgraph_viff import Point
from .pyqtgraph_viff import ItemGroup

from .SliceBox import *
from .ImageItemMod import *


class SliceWidget(GraphicsLayoutWidget):
    """
    Image widget to display slices of brain.
    First load image to canvas, constrain panning
    on mouse drag, change cursor and update image slices.
    """
    # Crosshair position changed.
    sigCPChanged = QtCore.Signal(list)
    # Cursor position changed.
    sigMouseOver = QtCore.Signal(list)
    # Slice focused.
    sigSelected = QtCore.Signal()

    def __init__(self, slice_type='c'):

        super(SliceWidget, self).__init__()

        # Modified ViewBox Widget
        self.sb = SliceBox()

        self.sb.setAspectLocked(True)
        self.addItem(self.sb)

        # Removes small black margins around the views.
        self.ci.layout.setContentsMargins(1, 1, 1, 1)
        self.ci.layout.setSpacing(1)

        self.image_dimensions = [0, 0, 0]
        self.crosshair_pos = [0, 0, 0]
        self.mouse_pos = [0, 0]

        self.image_count = 0
        self.slice = slice_type

        # foreground to catch mouse drag event
        self.foreground = ImageItemMod()

        self.initWidget()
        self.initCrosshair()

    def zoomIn(self):
        self.sb.zoom(0.9)

    def zoomOut(self):
        self.sb.zoom(1.1)

    def initWidget(self):
        """
        Initializations, set ImageItemMods and SliceBox
        """
        self.sb.addItem(self.foreground)
        self.foreground.setZValue(1000)
        self.foreground.setCompositionMode(
            QtGui.QPainter.CompositionMode_SourceOver)
        self.foreground.setImage(np.zeros((100,100,4)))

    def keyPressEvent(self, event):
        if type(event) == QtGui.QKeyEvent:
            # print(event.key())
            if event.key() == 16777234: # left
                self.crosshair_pos[0] -= 1
                self.sendCPSignal()
            if event.key() == 16777236: # right
                self.crosshair_pos[0] += 1
                self.sendCPSignal()
            if event.key() == 16777235: # up
                self.crosshair_pos[1] += 1
                self.sendCPSignal()
            if event.key() == 16777237: # down
                self.crosshair_pos[1] -= 1
                self.sendCPSignal()
            if event.key() == 16777238 or event.key() == 46: # page up
                self.crosshair_pos[2] += 1
                self.sendCPSignal()
            if event.key() == 16777239 or event.key() == 44: # page down
                self.crosshair_pos[2] -= 1
                self.sendCPSignal()
            event.accept()
        else:
            event.ignore()

    def focusOutEvent(self, event):
        self.v_line.setPen(mkPen({'color': "FF0", 'width': 1}))
        self.h_line.setPen(mkPen({'color': "FF0", 'width': 1}))

    def focusInEvent(self, event):
        self.v_line.setPen(mkPen({'color': "0F0", 'width': 1}))
        self.h_line.setPen(mkPen({'color': "0F0", 'width': 1}))
        self.sigSelected.emit()

    def reportMouseCursorPos(self, ev):
        coordinates = self.foreground.mapFromScene(ev)
        self.mouse_pos = [int(coordinates.x()), int(coordinates.y())]
        coord_x = int(coordinates.x()) + 0.5
        coord_y = int(coordinates.y()) + 0.5
        if self.slice == 'c':
            self.sigMouseOver.emit([coord_x, None, coord_y])
        if self.slice == 's':
            self.sigMouseOver.emit([None, coord_x,  coord_y])
        if self.slice == 't':
            self.sigMouseOver.emit([coord_x, coord_y, None])

    ## Crosshair stuff ##
    def initCrosshair(self):
        """
        Adds crosshair to SliceWidget.
        """
        self.v_line = InfiniteLine(angle=90, movable=False)
        self.h_line = InfiniteLine(angle=0, movable=False)
        self.v_line.setZValue(9000)
        self.h_line.setZValue(9000)
        self.sb.addItem(self.v_line)
        self.sb.addItem(self.h_line)

    def setCrosshairVisible(self, state):
        """
        Set the visibility of the crosshair.
        """
        self.v_line.setVisible(state)
        self.h_line.setVisible(state)

    def setCrosshairLines(self):
        """
        Reset crosshair lines.
        """
        self.v_line.setPos(self.crosshair_pos[0]+0.5)
        self.h_line.setPos(self.crosshair_pos[1]+0.5)
        self.sb.setZoomCenter(
            [self.crosshair_pos[0]+0.5, self.crosshair_pos[1]+0.5])

    def setCrosshairPos(self, pos):
        """
        Reset the crosshair position
        """
        self.crosshair_pos = pos
        self.setCrosshairLines()

    def getCrosshairPos(self):
        return self.crosshair_pos

    def sendCPSignal(self):
        """
        Send position of crosshair together with signal when moved.
        """
        if self.slice == 'c':
            self.sigCPChanged.emit(
                [self.crosshair_pos[0], self.crosshair_pos[2],
                 self.crosshair_pos[1]])
        if self.slice == 's':
            self.sigCPChanged.emit(
                [self.crosshair_pos[2], self.crosshair_pos[0],
                 self.crosshair_pos[1]])
        if self.slice == 't':
            self.sigCPChanged.emit(
                [self.crosshair_pos[0], self.crosshair_pos[1],
                 self.crosshair_pos[2]])

    def CrosshairMoved(self, ev):
        """
        Change crosshair coordinates when left clicked.
        """
        if ev.button() & QtCore.Qt.LeftButton:
            coordinates = self.foreground.mapFromScene(ev.scenePos())
            self.crosshair_pos[0] = int(coordinates.x())
            self.crosshair_pos[1] = int(coordinates.y())
            self.sendCPSignal()

    ## Managing Images and Dimensions ##
    def getForegroundSize(self):
        return self.foreground.image.shape

    def setImageDimensions(self, dimensions):
        """
        Resets image dimensions and foreground size.
        """
        self.image_dimensions = dimensions
        self.foreground.setImage(
            np.zeros((np.int(self.image_dimensions[0]),np.int(self.image_dimensions[1]),4)))

    def addImageItem(self, image_item):
        """
        Appends new ImageItemMod to the SliceBox.
        """
        self.sb.addItem(image_item)
        image_item.sigImageChanged.connect(self.update)
        self.image_dimensions[0:1] = image_item.image.shape
        # Resizing foreground might not be necessary.
        self.foreground.setImage(
            np.zeros((self.image_dimensions[0],self.image_dimensions[1],4)))
        if self.image_count is 0:
            self.foreground.sigMouseDrag.connect(self.CrosshairMoved)
            self.foreground.scene().sigMouseMoved.connect(
                self.reportMouseCursorPos)
            self.foreground.scene().sigMouseClicked.connect(self.CrosshairMoved)
        self.image_count += 1

    def removeImageItem(self, image_item):
        """
        Removes ImageItemMod from the SliceBox.
        """
        self.image_count -= 1
        self.sb.removeItem(image_item)
        if self.image_count is 0:
            self.foreground.sigMouseDrag.disconnect()
            self.foreground.scene().sigMouseMoved.disconnect()
            self.foreground.scene().sigMouseClicked.disconnect()
        self.update()

    def useMenu(self, menu):
        self.sb.useMyMenu(menu)

def main():

    # Tests
    app = QtGui.QApplication(sys.argv)

    low_pos = np.array([0.0, 1e-12, 1])
    low_color = np.array(
        [[0,0,0,0], [0,0,0,255], [255, 255, 255, 255]], dtype=np.ubyte)
    low_map = ColorMap(low_pos, low_color)
    low_lut = low_map.getLookupTable(0.0, 1.0, 256, alpha=True)

    print(low_lut)

    image1 = np.load('../templates/underlay1.npy')
    image2 = np.load('../templates/overlay1.npy')
    low_values_indices = image1 < 0
    image1[low_values_indices] = 0
    low_values_indices = image2 < 0
    image2[low_values_indices] = 0
    high_values_indices = image2 < 3
    image2[high_values_indices] = 0
    print(image1.max())
    print(image2.max())
    [rgba, truth] = makeARGB(image2, low_lut, levels=[3, 6], useRGBA=True)

    # Create ImageItems
    img1 = ImageItemMod.ImageItemMod()
    img1.setImage(image1)
    img1.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
    img2 = ImageItemMod.ImageItemMod()
    img2.setImage(rgba)
    img2.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)

    img1.setZValue(-1)
    img2.setZValue(1)

    widget = SliceWidget()
    widget.setCrosshairPosition([0,0])
    widget.addImageItem(img2)
    widget.addImageItem(img1)
    widget.update()
    widget.removeImageItem(img2)
    widget.removeImageItem(img1)
    widget.update()

    #widget.addImage(image)
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
