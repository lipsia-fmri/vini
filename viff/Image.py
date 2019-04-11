import sys, os.path
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import numpy.ma as ma
from nibabel import load
from nibabel.affines import apply_affine
from nibabel.volumeutils import shape_zoom_affine
from nibabel import Nifti1Image
import copy

import pyqtgraph as pg
from pyqtgraph.colormap import ColorMap

import ImageItemMod
import ColorMapWidget
import ImageDialog
from resample import resample_image
from quaternions import fillpositive, quat2mat, mat2quat

# try:
#     from pyvista import pyvista
# except ImportError:
#     pass


class Image(object):
    """
    This Image class is used to derive Image3D and Image4D to manage 3 and 4
    dimensional images.
    """

    def __init__(self, filename=None):

        # filename string
        self.image_path = filename
        # image object, Nifti1Image
        self.image = None
        # affine used for coordinate system
        self.affine_used = None
        # resample image data
        self.image_res = None
        self.res_shape = None
        # affine used for resampling (voxel coordinates)
        self.affine_res = None
        # affine used for resampling (voxel coordinates)
        self.affine_res_inv = None
        # 0 for nearest and 1 for linear
        self.interp_type = 0
        
        #sform code
        self.sform_code = -1

        # For resample to fit, the affine is overwritten with this:
        self.state_affine_over = False

        # Saves where to saturate of clip values.
        self.clippings_pos = [False, False]
        self.clippings_neg = [False, False]

        # Saves whether image should be displayed.
        self.state = True
        # Coordinates of the image slices.
        self.coord = [0,0,0]
        self.two_cm = True
        self.image_slices_pos = [None, None, None]
        self.image_slices_neg = [None, None, None]
        self.image_slices = [None, None, None]

        self.threshold_pos = [0.0, 0.0]
        self.threshold_neg = [0.0, 0.0]
        self.cmap_pos = None
        self.cmap_neg = None
        self.hist_saved = False

        # Has to be kept up to date when resampling or changing frame (4D).
        self.extremum = [0, 0]
        self.deadzone = 1e-7 #for two colormaps: excludes values from negative cmap (otherwise 0 = blue)

        # Use as an alpha for the whole image.
        self.alpha = 1.0
        self.mode = QtGui.QPainter.CompositionMode_SourceOver

        # Clippings for histograms
        # Not needed anymore?
        self.hist_clips = [0, 0]

        # Dialog for changing properties
        self.dialog = ImageDialog.ImageDialog()
        self.dialog.sigPreferencesSave.connect(self.changedProperties)
        self.dialog.sigDiscreteCM.connect(self.useDiscreteCM)

        # Positive and negative color map widgets
        self.pos_gradient = ColorMapWidget.ColorMapWidget()
        self.pos_gradient.sigGradientChanged.connect(self.setColorMapPos)
        self.neg_gradient = ColorMapWidget.ColorMapWidget()
        self.neg_gradient.sigGradientChanged.connect(self.setColorMapNeg)

        self.pos_gradient.item.loadPreset('grey')
        self.neg_gradient.item.loadPreset('grey')

        # This can only be set after initilizing the gradients.
        self.dialog.setPreferences(
        alpha=self.alpha, interp=self.interp_type, two_cm=self.two_cm,
        mode=self.mode, clippings_pos =self.clippings_pos,
        clippings_neg=self.clippings_neg)

        if filename is not None:
            self.loadImage(filename)

    def loadImageFromObject(self, img):
        """
        Dummy function to be overwritten by derived classes.
        """
        pass

    def type(self):
        """
        Dummy function to be overwritten by derived classes.
        """
        pass

    def loadImage(self, image_data, affine):
        """
        Creates image from given numpy array and affine (4x4 numpy array)
        """
        self.image = Nifti1Image(image_data, affine)
        self.resample()

    def getBounds(self):
        """
        Returns the bounds of the image in the coordinate system wrt. the
        affine transformation.
        """
        adim, bdim, cdim = self.image.shape
        adim -= 1
        bdim -= 1
        cdim -= 1
        # form a collection of vectors for each 8 corners of the box
        box = np.array([[0.,   0,    0,    1],
                        [adim, 0,    0,    1],
                        [0,    bdim, 0,    1],
                        [0,    0,    cdim, 1],
                        [adim, bdim, 0,    1],
                        [adim, 0,    cdim, 1],
                        [0,    bdim, cdim, 1],
                        [adim, bdim, cdim, 1]]).T
        box = np.dot(self.image.affine, box)[:3]
        return list(zip(box.min(axis=-1), box.max(axis=-1)))

    def calculateQFormAffine(self, pixdim, qform_code, quats):
        """
        Returns the qform.
        """
        bcd = [quats[0], quats[1], quats[2]]
        quaternion_threshold = -np.finfo(np.float32).eps * 3
        quaternions = fillpositive(bcd, quaternion_threshold)
        R = quat2mat(quaternions)
        vox = np.copy(pixdim[1:4])
        if np.any(vox) < 0:
            raise IOError("pixdim[1,2,3] should be positive")
        qfac = pixdim[0]
        if qfac not in (-1, 1):
            raise IOError("qfac (pixdim[0]) should be -1 or 1")
        vox[-1] *= qfac
        S = np.diag(vox)
        M = np.dot(R, S)
        out = np.eye(4)
        out[0:3, 0:3] = M
        out[0:3, 3] = [quats[3], quats[4], quats[5]]
        return out

    def getOriginalDimensions(self):
        return self.image.get_data().shape

    def getDimensions(self):
        return self.image_res.shape

    def updateCoordinates(self, coord=[0, 0, 0]):
        """
        Updates the internal coordinates with those of the viewer and reslices.
        """
        self.coord = coord
        if self.state:
            self.slice()

    def getState(self):
        return self.state

    def activate(self):
        self.state = True
        self.slice()

    def deactivate(self):
        self.state = False

    def setThresholdsDefault(self):
        """
        Resets the default thresholds.
        """
        self.setPosThresholdsDefault()
        self.setNegThresholdsDefault()

    def setPosThresholdsDefault(self):
        if self.extremum[1] < 0:
            self.threshold_pos = [0.0, 0.0]
        else:
            self.threshold_pos = [0.0, self.extremum[1]]
            # discontinued choice: intelligent upper threshold
            # if self.upper is None:
            #     length = self.image.get_data().size
            #     random_sample = np.random.randint(0, length, 10000)
            #     random_sample_unr = np.unravel_index(random_sample, self.image.get_data().shape)
            #     samples = self.image.get_data()[random_sample_unr]
            #     self.upper = np.percentile(samples, 99.9)

    def setNegThresholdsDefault(self):
        if self.extremum[0] >= 0:
            self.threshold_neg = [-self.deadzone, -self.deadzone]
        else:
            self.threshold_neg = [self.extremum[0], -self.deadzone]

    def setPosThresholdsFromSlider(self, lower_value, upper_value):
        """
        Set positive thresholds from slider value.
        """
        self.threshold_pos = list(self.threshold_pos)
        self.threshold_pos[0] = (lower_value)/1000.0 * self.extremum[1] +self.deadzone
        self.threshold_pos[1] = (upper_value)/1000.0 * self.extremum[1] +self.deadzone

    def setNegThresholdsFromSlider(self, lower_value, upper_value):
        """
        Set negative thresholds from slider value.
        """
        self.threshold_neg = list(self.threshold_neg)
        self.threshold_neg[0] = (upper_value)/1000.0 * self.extremum[0] -self.deadzone
        self.threshold_neg[1] = (lower_value)/1000.0 * self.extremum[0] -self.deadzone

    def setPosThresholds(self, threshold):
        """
        Sets the positive thresholds.
        """
        self.threshold_pos = copy.copy(threshold)

    def setNegThresholds(self, threshold):
        """
        Sets the negative thresholds.
        """
        self.threshold_neg = copy.copy(threshold)

    def getPosSldValueLow(self):
        """
        Computes the positive lower slider value.
        """
        tick_length = self.extremum[1]/1000.0 - self.deadzone 
        if tick_length == 0:
            return 1000
        else:
            return int(self.threshold_pos[0]/tick_length)

    def getPosSldValueHigh(self):
        """
        Computes the positive higher slider value.
        """
        tick_length = self.extremum[1]/1000.0 + self.deadzone 
        if tick_length == 0:
            return 1000
        else:
            return int(self.threshold_pos[1]/tick_length)

    def getNegSldValueLow(self):
        """
        Computes the negative lower slider value.
        """
        tick_length = self.extremum[0]/1000.0
        if tick_length == 0:
            return 1000
        else:
            return int(self.threshold_neg[0]/tick_length)

    def getNegSldValueHigh(self):
        """
        Computes the negative higher slider value.
        """
        tick_length = self.extremum[0]/1000.0
        if tick_length == 0:
            return 1000
        else:
            return int(self.threshold_neg[1]/tick_length)

    def setInterpolation(self, interp_type):
        self.interp_type = interp_type

    def presetCMPos(self, name):
        """
        Loads a predefined positive colormap with the name name.
        """
        self.pos_gradient.item.loadPreset(name)

    def presetCMNeg(self, name):
        """
        Loads a predefined negative colormap with the name name.
        """
        self.neg_gradient.item.loadPreset(name)

    def setClippingsPos(self, clpg_low, clpg_high):
        self.clippings_pos = [clpg_low, clpg_high]

    def setClippingsNeg(self, clpg_low, clpg_high):
        self.clippings_neg = [clpg_low, clpg_high]

    # Resample with given affine
    def resample_overaffine(self, shape, t_affine, over_affine):
        """
        Resamples the image to 'shape' with the transformation 'affine'
        overwriting its own transformation with 'over_affine'.
        """
        self.affine_res_inv = np.dot(np.linalg.inv(over_affine), t_affine)
        self.image_res = resample_image(
            self.image.get_data(), affine=self.affine_res_inv,
            shape=shape, interpolation=self.interp_type)
        self.res_shape = shape
        self.state_affine_over = True

    def resample(self, shape, affine):
        """
        Resamples the image to 'shape' with the transformation 'affine'.
        """
        self.affine_res_inv = np.dot(np.linalg.inv(self.image.affine), affine)
        self.image_res = resample_image(
            self.image.get_data(), affine=self.affine_res_inv,
            shape=shape, interpolation=self.interp_type)
        self.res_shape = shape
        self.state_affine_over = False

    def reresample(self):
        """
        Resamples with already given affine.
        """
        self.image_res = resample_image(
            self.image.get_data(), affine=self.affine_res_inv,
            shape=self.res_shape, interpolation=self.interp_type)

    def getAffine(self):
        return self.image.affine

    # probably not used?
    def getAffineUsed(self):
        return self.affine_res_inv

    def getVoxelCoords(self, m):
        """
        Return original voxel coordinates of the coordinates in m.
        """
        if self.affine_res_inv is not None:
            xyz = np.array([m[0], m[1], m[2], 1])
            mapped_xyz = np.dot(self.affine_res_inv, xyz)
            return mapped_xyz
        else:
            print("Image doesn't have a affine inverse used for resampling \
            yet!")

    def setUnresampled(self):
        # TODO: setze self.affine_res_inv = np.eye(4)?
        self.image_res = self.image.get_data()

    def setHistogram(self):
        c_hist = self.getHistogram()

    def slice(self, coord=None):
        """
        Slices through the resampled data cube and applies the colormaps.
        """
        if self.image_res is None:
            return 0
        if coord is not None:
            self.coord = coord

        if not self.state:
            return 0

        [self.image_slices_pos[0], truth] = \
            pg.mymakeARGB(
                self.image_res[int(self.coord[0]),:,:], lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)
        [self.image_slices_pos[1], truth] = \
            pg.mymakeARGB(
                self.image_res[:,int(self.coord[1]),:], lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)
        [self.image_slices_pos[2], truth] = \
            pg.mymakeARGB(
                self.image_res[:,:,int(self.coord[2])], lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)

        if self.two_cm:
            [self.image_slices_neg[0], truth] = \
                pg.mymakeARGB(
                    self.image_res[int(self.coord[0]),:,:], self.cmap_neg,
                    levels=[self.threshold_neg[0], self.threshold_neg[1]],
                    useRGBA=True)
            [self.image_slices_neg[1], truth] = \
                pg.mymakeARGB(
                    self.image_res[:,int(self.coord[1]),:], self.cmap_neg,
                    levels=[self.threshold_neg[0], self.threshold_neg[1]],
                    useRGBA=True)
            [self.image_slices_neg[2], truth] = \
                pg.mymakeARGB(
                    self.image_res[:,:,int(self.coord[2])], self.cmap_neg,
                    levels=[self.threshold_neg[0], self.threshold_neg[1]],
                    useRGBA=True)

        # add positive and negative parts
        if (self.two_cm and
                float(self.threshold_neg[0]) != float(self.threshold_neg[1])):
            self.image_slices[0] = \
                self.image_slices_pos[0] + self.image_slices_neg[0]
            self.image_slices[1] = \
                self.image_slices_pos[1] + self.image_slices_neg[1]
            self.image_slices[2] = \
                self.image_slices_pos[2] + self.image_slices_neg[2]
        else:
            self.image_slices[0] = self.image_slices_pos[0]
            self.image_slices[1] = self.image_slices_pos[1]
            self.image_slices[2] = self.image_slices_pos[2]

    def mosaicSlice(self, plane, coord):
        """
        Returns slices for the mosaic view.
        """
        sliced = None
        if plane == 's':
            sliced = self.image_res[coord,:,:]
        if plane == 'c':
            sliced = self.image_res[:,coord,:]
        if plane == 't':
            sliced = self.image_res[:,:,coord]
        [slice_rgba, truth] = pg.mymakeARGB(
            sliced, self.cmap_pos, levels=[self.threshold_pos[0],
            self.threshold_pos[1]], useRGBA=True)
        if (self.two_cm and
                float(self.threshold_neg[0]) != float(self.threshold_neg[1])):
            [slice_neg, truth] = pg.mymakeARGB(
                sliced, self.cmap_neg, levels=[self.threshold_neg[0],
                self.threshold_neg[1]], useRGBA=True)
            slice_rgba = np.add(slice_rgba, slice_neg)
        return slice_rgba

    def getImageArrays(self):
        return self.image_slices

    def setColorMapPos(self, color_map=None):
        """
        Changes the positive colormap.
        """
        color_map = self.pos_gradient.item.getLookupTable(512, alpha=True)
        color_map[:,3] = int(255.0*self.alpha)
        alpha_out = np.zeros((1,4))
        if self.clippings_pos[0]:
            color_map = np.concatenate((alpha_out, color_map), axis=0)
        if self.clippings_pos[1]:
            color_map = np.concatenate((color_map, alpha_out), axis=0)
        self.cmap_pos = color_map
        self.slice()

    def setColorMapNeg(self, color_map=None):
        """
        Changes the negative colormap.
        """
        color_map = self.neg_gradient.item.getLookupTable(512,True)
        color_map[:,3] = int(255.0*self.alpha)
        # Hack: turn around negative colormap:
        color_map = color_map[::-1,:]
        alpha_out = np.zeros((1,4))
        if self.clippings_neg[0]:
            color_map = np.concatenate((alpha_out, color_map), axis=0)
        if self.clippings_neg[1]:
            color_map = np.concatenate((color_map, alpha_out), axis=0)
        self.cmap_neg = color_map
        self.slice()

    def useDiscreteCM(self):
        """
        Define colormap for discrete intensity values.
        """
        value_set = np.unique(self.image.get_data())
        if value_set.size <= 256:
            value_set = np.subtract(value_set, value_set[0])
            value_set = np.multiply(value_set, 1./value_set[-1])
            colors = []
            for i in range(0,value_set.size):
                cc = QtGui.QColor()
                cc.setHsv(int(i*255.0/value_set.size), 200, 255, alpha=255.0)
                colors.append(
                    [cc.red(), cc.green(), cc.blue(), int(255*self.alpha)])
            cm = ColorMap(value_set, np.array(colors, dtype=np.ubyte))
            # sets the gradient correctly
            self.pos_gradient.item.setColorMap(cm)
            # uses the gradient to get the actual colormap and slices
            self.setColorMapPos()
        else:
            QtGui.QMessageBox.warning(self, "Warning",
                "Warning: Image has more than 256 different values.")

    def hide_gradients(self):
        self.pos_gradient.hide()
        self.neg_gradient.hide()

    def getIntensity(self, coord=None):
        """
        Returns the intensity at the current coordinate.
        """
        if coord is not None:
            return self.image_res[int(coord[0]),int(coord[1]),int(coord[2])]
        else:
            return self.image_res[int(self.coord[0]),int(self.coord[1]),
                                  int(self.coord[2])]

    def getHistogram(self, targetHistogramSize=500):
        """
        Returns a histogram (two arrays with bin values and bin positions) of
        the currently resampled image.
        """
        if self.hist_saved is not True:
            xmin = self.getMin()
            xmax = self.getMax()
            hist_bins = np.linspace(xmin, xmax, targetHistogramSize)
            self.hist = np.histogram(self.image_res[self.image_res!=0], bins=hist_bins)
            self.hist_saved = True
        return self.hist[1][:-1], self.hist[0]

    def getYRangeApprox(self):
        """
        Returns a y range for the current histogram that scales the plot
        reasonably.
        """
        if self.hist_saved is not True:
            self.getHistogram()
        valid_bins = np.logical_and(
            self.hist[1][:-1] > self.threshold_pos[0],
            self.hist[1][:-1] < self.threshold_pos[1])
        valid_values = self.hist[0][valid_bins]
        # catch the case of no valid values
        if valid_values.size != 0:
            yrange = [np.min(valid_values), np.max(valid_values)]
        else:
            yrange = [np.min(self.hist[0]), np.max(self.hist[0])]
        return yrange

    def getMin(self):
        return self.extremum[0]

    def getMax(self):
        return self.extremum[1]

    def getMaxCoord(self, radius=0):
        """
        Return the coordinate of the local maximum within a cube of given width.
        """
        if (radius == 0):
            return list(np.unravel_index(
                self.image_res.argmax(), self.image_res.shape))
        else:
            shapes = self.image_res.shape
            x_range = range(max(0, self.coord[0]-radius),
                            min(self.coord[0]+radius, shapes[0]))
            y_range = range(max(0, self.coord[1]-radius),
                            min(self.coord[1]+radius, shapes[1]))
            z_range = range(max(0, self.coord[2]-radius),
                            min(self.coord[2]+radius, shapes[2]))
            new_shape = [x_range[-1]-x_range[0]+1,
                         y_range[-1]-y_range[0]+1,
                         z_range[-1]-z_range[0]+1]
            arg_max = \
                self.image_res[x_range,:,:][:,y_range,:][:,:,z_range]\
                .argmax()
            arg_coord = list(np.unravel_index(arg_max, new_shape))
            arg_coord[0] += x_range[0]
            arg_coord[1] += y_range[0]
            arg_coord[2] += z_range[0]
            return arg_coord

    def getMinCoord(self, radius=0):
        """
        Return the coordinate of the local minimum within a cube of given width.
        """
        if (radius == 0):
            return list(np.unravel_index(
                self.image_res.argmin(), self.image_res.shape))
        else:
            shapes = self.image_res.shape
            x_range = range(max(0, self.coord[0]-radius),
                            min(self.coord[0]+radius, shapes[0]))
            y_range = range(max(0, self.coord[1]-radius),
                            min(self.coord[1]+radius, shapes[1]))
            z_range = range(max(0, self.coord[2]-radius),
                            min(self.coord[2]+radius, shapes[2]))
            new_shape =  [x_range[-1]-x_range[0]+1,
                          y_range[-1]-y_range[0]+1,
                          z_range[-1]-z_range[0]+1]
            arg_max = \
                self.image_res[x_range,:,:][:,y_range,:][:,:,z_range]\
                .argmin()
            arg_coord = list(np.unravel_index(arg_max, new_shape))
            arg_coord[0] += x_range[0]
            arg_coord[1] += y_range[0]
            arg_coord[2] += z_range[0]
            return arg_coord

    def openDialog(self):
        """
        Open image dialog.
        """
        self.dialog.exec_()

    def writeProps(self):
        """
        Write preferences to dialog.
        """
        self.dialog.setPreferences(
            alpha=self.alpha, interp=self.interp_type, two_cm=self.two_cm,
            mode=self.mode, clippings_pos =self.clippings_pos,
            clippings_neg=self.clippings_neg)

    def changedProperties(self):
        """
        Get changed values from dialog.
        """
        self.alpha = self.dialog.getAlpha()
        self.mode = self.dialog.comp_mode
        if self.interp_type != self.dialog.getInterpolation():
            self.interp_type = self.dialog.getInterpolation()
            self.reresample()
        self.two_cm = self.dialog.getColormapNo()
        self.clippings_pos = self.dialog.getClipsPos()
        self.clippings_neg = self.dialog.getClipsNeg()
        self.setColorMapPos()
        self.setColorMapNeg()
        self.slice()
