from pyqtgraph.Qt import QtCore, QtGui
import sys
import os.path
import numpy as np
from nibabel import load
from nibabel.affines import apply_affine
from nibabel.volumeutils import shape_zoom_affine
from nibabel import Nifti1Image
import copy

import pyqtgraph as pg

import FunctionalDialog
import AveragePlot
from Image import Image
from resample import resample_image
from TimePlot import TimePlot
from testInputs import testFloat, testInteger
# try:
#     from pyvista import pyvista
# except ImportError:
#     pass


class Image4D(Image):
    """
    Class to store 4 dimensional images.
    """

    def __init__(self, **kwargs):

        super(Image4D, self).__init__(filename=None)

        # Frame: from 0 to time_dim-1
        self.frame = 0
        self.time_dim = 1
        # better call this TR?
        self.frame_time = 1
        self.image_slice_res = [None, None, None]

        # while playing don't use the fully resampled image for slices
        # This might not be needed  anymore
        self.playing = False

        # Variables for possible windows.
        self.timeseries = None
        self.time_averages = None
        self.design = None

        self.funcdialog = FunctionalDialog.FunctionalDialog()
        self.funcdialog.sigChanged.connect(self.changedFuncProperties)
        self.funcdialog.sigDelDesMat.connect(self.delDesignFile)
        self.funcdialog.sigDesignFile.connect(self.openDesignFile)
        self.funcdialog.sigComputeTA.connect(self.computeTA)

        if 'filename' in kwargs:
            self.loadImageFromFile(kwargs['filename'])
        if 'image' in kwargs:
            self.loadImageFromObject(kwargs['image'], kwargs['color'])

    def type(self):
        """
        Returns a string to say whether it has one or two color maps
        """
        if self.two_cm:
            return "two"
        else:
            return "one"

    def type_d(self):
        return "4D"

    def loadImageFromObject(self, img, color=False):

        self.image = img

        self.image_res = img.get_data()[:,:,:,self.frame]
        self.time_dim = img.get_data().shape[3] # set beginning from zero.

        self.extremum[0] = img.get_data().min()
        self.extremum[1] = img.get_data().max()

        self.two_cm = color
        self.dialog.setPreferences(two_cm=self.two_cm, clippings_pos=self.clippings_pos, clippings_neg=self.clippings_neg)

        self.setPosThresholdsDefault()
        self.setNegThresholdsDefault()
        self.slice()

    def getIntensity(self, coord=None):
        """
        Returns the intensity at the current coordinate.
        """
        if self.playing == False:
            if coord is not None:
                coord = map(lambda x: int(x),coord)
                return self.image_res[coord[0],coord[1],coord[2]]
            else:
                return self.image_res[self.coord[0],self.coord[1],self.coord[2]]
        else:
            # while in play mode no intensity values are displayed
            return np.nan

    def getOriginalDimensions(self):
        return self.image.get_data().shape[0:3]

    def getDimensions(self):
        return self.image_res.shape[0:3]

    def getTimeDim(self):
        return self.time_dim

    def getFrame(self):
        """ Return index of time beginning from zero. """
        return self.frame

    def setFrame(self, new_frame=0):
        if new_frame >= 0 and new_frame < self.time_dim:
            self.frame = new_frame
            self.hist_saved = False

    def getBounds(self):
        adim, bdim, cdim = self.image.shape[0:3]
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

    def resample_overaffine(self, shape, t_affine, over_affine):
        """
        Resamples the image to 'shape' with the transformation 'affine'
        overwriting its own transformation with 'over_affine'.
        """
        self.affine_res_inv = np.dot(np.linalg.inv(over_affine), t_affine)
        self.res_shape = shape
        self.image_res = resample_image(
            self.image.get_data()[:,:,:,self.frame],
            affine=self.affine_res_inv, shape=shape,
            interpolation=self.interp_type)
        self.state_affine_over = True

    def resample(self, shape, affine):
        """
        Resamples the image to 'shape' with the transformation 'affine'.
        """
        t_affine = np.dot(np.linalg.inv(self.image.affine), affine)
        self.res_shape = shape
        self.image_res = resample_image(
            self.image.get_data()[:,:,:,self.frame], affine=t_affine,
            shape=shape, interpolation=self.interp_type)
        self.affine_res_inv = np.dot(np.linalg.inv(self.image.affine), affine)
        self.state_affine_over = False

    def reresample(self):
        """
        Resample frame with already known affine.
        """
        self.image_res = resample_image(
            self.image.get_data()[:,:,:,self.frame],
            affine=self.affine_res_inv, shape=self.res_shape,
            interpolation=self.interp_type)

    def resample_frame(self):
        """
        Same as reresample???
        """
        self.image_res = resample_image(
            self.image.get_data()[:,:,:,self.frame],
            affine=self.affine_res_inv, shape=self.res_shape,
            interpolation=self.interp_type)

    def resample_slice(self, shape, affine):
        """
        Resamples only current slices.
        """
        
        t_affine = np.dot(np.linalg.inv(self.image.affine), affine)
        if self.state_affine_over:
            # TODO: use this as default without if-clause?
            # doesn't hurt to leave this here
            t_affine = self.affine_res_inv

        n_coord = np.dot(t_affine[0:3,0:3], self.coord)
        n_coord = np.zeros((3,1))
        n_coord[0] = self.coord[0]
        shift = np.dot(t_affine[0:3,0:3], n_coord)
        t_affine_0 = np.copy(t_affine)
        t_affine_0[0:3][:,3:4] = np.add(t_affine_0[0:3][:,3:4], shift)
        shape_0 = np.copy(shape)
        shape_0[0] = 1
        self.image_slice_res_sa = resample_image(
            self.image.get_data()[:,:,:,self.frame], affine=t_affine_0,
            shape=shape_0, interpolation=self.interp_type)[0,:,:]
        
        self.xhairval = self.image_slice_res_sa[self.coord[1], self.coord[2]]
        
        n_coord = np.zeros((3,1))
        n_coord[1] = self.coord[1]
        shift = np.dot(t_affine[0:3,0:3], n_coord)
        t_affine_1 = np.copy(t_affine)
        t_affine_1[0:3][:,3:4] = np.add(t_affine_1[0:3][:,3:4], shift)
        shape_1 = np.copy(shape)
        shape_1[1] = 1
        
       
        
        self.image_slice_res_co = resample_image(
            self.image.get_data()[:,:,:,self.frame], affine=t_affine_1,
            shape=shape_1, interpolation=self.interp_type)[:,0,:]
        n_coord = np.zeros((3,1))
        n_coord[2] = self.coord[2]
        shift = np.dot(t_affine[0:3,0:3], n_coord)
        t_affine_2 = np.copy(t_affine)
        t_affine_2[0:3][:,3:4] = np.add(t_affine_2[0:3][:,3:4], shift)
        shape_2 = np.copy(shape)
        shape_2[2] = 1
        self.image_slice_res_tr = resample_image(
            self.image.get_data()[:,:,:,self.frame], affine=t_affine_2,
            shape=shape_2, interpolation=self.interp_type)[:,:,0]

        [self.image_slices_pos[0], truth] = \
            pg.makeARGB(
                self.image_slice_res_sa, lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)
        [self.image_slices_pos[1], truth] = \
            pg.makeARGB(
                self.image_slice_res_co, lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)
        [self.image_slices_pos[2], truth] = \
            pg.makeARGB(
                self.image_slice_res_tr, lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)

        if self.two_cm:
            [self.image_slices_neg[0], truth] = \
                pg.makeARGB(
                    self.image_slice_res_sa, self.cmap_neg,
                    levels=[self.threshold_neg[0], self.threshold_neg[1]],
                    useRGBA=True)
            [self.image_slices_neg[1], truth] = \
                pg.makeARGB(
                    self.image_slice_res_co, self.cmap_neg,
                    levels=[self.threshold_neg[0], self.threshold_neg[1]],
                    useRGBA=True)
            [self.image_slices_neg[2], truth] = \
                pg.makeARGB(
                    self.image_slice_res_tr, self.cmap_neg,
                    levels=[self.threshold_neg[0], self.threshold_neg[1]],
                    useRGBA=True)

        # add positive and negative parts
        if (self.two_cm and
                float(self.threshold_neg[0]) != float(self.threshold_neg[1])):
            self.image_slices[0] = self.image_slices_pos[0] + self.image_slices_neg[0]
            self.image_slices[1] = self.image_slices_pos[1] + self.image_slices_neg[1]
            self.image_slices[2] = self.image_slices_pos[2] + self.image_slices_neg[2]
        else:
            self.image_slices[0] = self.image_slices_pos[0]
            self.image_slices[1] = self.image_slices_pos[1]
            self.image_slices[2] = self.image_slices_pos[2]
            
        

    def setPlaying(self, state):
        self.playing = state

    def slice(self, coord=None):
        if self.image_res is None:
            return 0
        if coord is not None:
            self.coord = coord
        if self.playing and not self.state:
            return 0

        self.updateTimeData()
        self.updateTimeAverageData()

        [self.image_slices_pos[0], truth] = \
            pg.makeARGB(
                self.image_res[self.coord[0],:,:], lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)
        [self.image_slices_pos[1], truth] = \
            pg.makeARGB(
                self.image_res[:,self.coord[1],:], lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)
        [self.image_slices_pos[2], truth] = \
            pg.makeARGB(
                self.image_res[:,:,self.coord[2]], lut=self.cmap_pos,
                levels=[self.threshold_pos[0], self.threshold_pos[1]],
                useRGBA=True)

        if self.two_cm:
            [self.image_slices_neg[0], truth] = \
                pg.makeARGB(
                    self.image_res[self.coord[0],:,:], self.cmap_neg,
                    levels=[self.threshold_neg[0], self.threshold_neg[1]],
                    useRGBA=True)
            [self.image_slices_neg[1], truth] = \
                pg.makeARGB(
                    self.image_res[:,self.coord[1],:], self.cmap_neg,
                    levels=[self.threshold_neg[0], self.threshold_neg[1]],
                    useRGBA=True)
            [self.image_slices_neg[2], truth] = \
                pg.makeARGB(
                    self.image_res[:,:,self.coord[2]], self.cmap_neg,
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

    def setTime(self, time):
        self.frame_time = 1 #time #TR =1 forever...

    def showTimeSeries(self, pos=(150,150,600,600)):
        """
        Opens time series plot.
        """
        if self.timeseries is None:
            self.timeseries = TimePlot(title=self.filename)
        self.timeseries.setGeometry(pos[0], pos[1], pos[2], pos[3])
        self.updateTimeData()
        self.timeseries.show()

    def openDesignFile(self, fname):
        """
        Displays file menu for opening a design file.
        """
        if fname != "":
            import csv
            self.design = []
            with open(fname, 'rb') as csvfile:
                design_file = open(fname)
                dialect = csv.Sniffer().sniff(design_file.read(1024))
                design_file.seek(0)
                reader = csv.reader(design_file, dialect)
                # reader = csv.reader(csvfile,delimiter='\t')
                for row in reader:
                    float_row = []
                    for i in row:
                        float_row.append(float(i))
                    self.design.append(float_row)
            if self.timeseries is None:
                self.timeseries = TimePlot()
            self.updateTimeData()
            if len(self.design) != 0:
                self.design = np.array(self.design)
                # create colors
                self.cond_colors = {}
                self.conds = np.unique(self.design[:,0]).astype(np.int)
                for i in range(len(self.conds)):
                    color = QtGui.QColor()
                    color.setHsv(
                        int(i*255.0/len(self.conds)), 200, 200, alpha=160)
                    self.cond_colors[self.conds[i]] = color
                self.timeseries.setDesign(self.design, self.cond_colors)
                # min value for default duration is 10
                if self.design[0,2] < 10.0:
                    self.funcdialog.setAverageSettings(10.0, self.conds)
                else:
                    self.funcdialog.setAverageSettings(
                        self.design[0,2], self.conds)

    def delDesignFile(self):
        """
        Removes the design file.
        """
        if self.timeseries is not None:
            self.timeseries.delDesign()
            self.design = None

    def updateTimeData(self):
        """
        Updates the time plot when the coordinate is changed.
        """
        if self.affine_res_inv is not None and self.timeseries is not None:
            xyz = np.array([self.coord[0], self.coord[1], self.coord[2], 1])
            map_xyz = np.dot(self.affine_res_inv, xyz).astype(np.int32)
            shp = self.image.get_data().shape
            # TODO: make this a shorter comparison
            if (map_xyz[0] >= 0 and map_xyz[0] < shp[0] and
                    map_xyz[1] >= 0 and map_xyz[1] < shp[1] and
                    map_xyz[2] >= 0 and map_xyz[2] < shp[2]):
                self.timeseries.setData(
                    self.image.get_data()[map_xyz[0],map_xyz[1],map_xyz[2],:],
                    self.frame_time)
            else:
                self.timeseries.setData(
                    np.zeros((self.time_dim)),self.frame_time)

    def openFuncDialog(self):
        """
        Opens the functional dialog.
        """
        if self.design is not None:
            # don't take the first condition length but 20 seconds as a default
            # min value for default duration is 10
            c_length = 10.0
            if self.design[0,2] >= 10.0:
                c_length = self.design[0,2]
            self.funcdialog.setPreferences(
                frame_time=self.frame_time, TR=self.frame_time,
                length=c_length, conds=self.conds)
        else:
            self.funcdialog.setPreferences(
                frame_time=self.frame_time, TR=self.frame_time)
        self.funcdialog.show()

    def changedFuncProperties(self):
        self.frame_time = self.funcdialog.getFrameTime()
        self.updateTimeData()

    def computeTA(self):
        """
        Computes averages over trials of the same experimental condition.
        """
        if self.design is not None:
            # for every experimental condition:
            self.num_pts = np.floor(
                self.funcdialog.cond_time/self.funcdialog.cond_dx)
            self.time_pts_cond = np.linspace(
                0, self.num_pts*self.funcdialog.cond_dx, self.num_pts)
            self.time_pts = np.linspace(
                0, (self.time_dim-1)*self.frame_time, self.time_dim)
            self.cond_conds = self.funcdialog.cond_conds
            # Delete those not in self.conds:
            if set(self.cond_conds) <= set(self.conds):
                pass
            else:
                QtGui.QMessageBox.warning(self.funcdialog, "Warning",
                    "Error: Condition not in design file. Removed.")
                self.cond_conds = list(
                    set(self.cond_conds).intersection(self.conds))

            self.num_cond = len(self.cond_conds)
            self.x_pos = []
            for cond in range(len(self.cond_conds)):
                self.x_pos.append([])
                for interval in self.design:
                    if interval[0] == self.cond_conds[cond]:
                        # append timepoints for this interval
                        self.x_pos[cond].append(self.time_pts_cond+interval[1])

            if self.time_averages is None:
                self.time_averages = AveragePlot.AveragePlot()
            # initialize plots & colors
            self.time_averages.reset()
            self.updateTimeAverageData()
            self.time_averages.show()
        else:
            QtGui.QMessageBox.warning(self.funcdialog, "Warning",
                "Error: No design file was loaded.")

    def updateTimeAverageData(self):
        """
        Updates the time average data if the coordinate is changed.
        """
        if self.affine_res_inv is not None and self.time_averages is not None:
            # set factor for stddev
            self.time_averages.setCStddev(self.funcdialog.cond_stddevs)
            # compute original data voxel
            xyz = np.array([self.coord[0], self.coord[1], self.coord[2], 1])
            map_xyz = np.dot(self.affine_res_inv, xyz)
            shp = self.image.get_data().shape
            # if voxel is in the data
            # TODO: make this a nicer comparison
            if (map_xyz[0] >= 0 and map_xyz[0] < shp[0] and
                    map_xyz[1] >= 0 and map_xyz[1] < shp[1] and
                    map_xyz[2] >= 0 and map_xyz[2] < shp[2]):
                # retrieve voxel data
                voxel_data = \
                    self.image.get_data()[map_xyz[0],map_xyz[1],map_xyz[2],:]
                # for every condition compute average over trials
                for cond in range(self.num_cond):
                    data = np.zeros((self.num_pts, len(self.x_pos[cond])))
                    for trial in range(len(self.x_pos[cond])):
                        data[:,trial] = np.interp(
                            self.x_pos[cond][trial], self.time_pts, voxel_data)
                    mean = data.mean(axis=1)
                    stderr = np.std(data, axis=1)/len(self.x_pos[cond])
                    # self.cond_conds[cond] is the actual condition number
                    self.time_averages.updateData(
                        self.cond_conds[cond], self.time_pts_cond, mean,
                        stderr, self.cond_colors[self.cond_conds[cond]])
            else:
                # flat line all lines
                zeros = np.zeros((self.time_pts_cond.shape))
                for cond in range(self.num_cond):
                    self.time_averages.updateData(
                        self.cond_conds[cond], self.time_pts_cond, zeros,
                        zeros, self.cond_colors[self.cond_conds[cond]])
