"""
Image loading function
This separates the viewer from nibabel and pyvista.
It takes loading preferences and a filename and gives back the correct image class.
"""

import sys
import os.path
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
from nibabel import load
from nibabel.affines import apply_affine
from nibabel.volumeutils import shape_zoom_affine
from nibabel import Nifti2Image

import pyqtgraph as pg

from resample import resample_image
import ImageItemMod
import ColorMapWidget
import ImageDialog
import Image3D
import Image4D
from VistaLoad import load_vista

# try:
#     import pyvista
# except ImportError:
#     print("Warning: import error, module pyvista is unavailable.")

from quaternions import fillpositive, quat2mat, mat2quat


def calculateQFormAffine(pixdim, qform_code, quats):
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

def loadImageFromNifti(fileobject, pref, f_type):

    color_cm = False
    if f_type != 0:
        color_cm = True
    try:
        image = Nifti2Image(fileobject.get_data(), fileobject.affine)
        hdr = fileobject.header
    except RuntimeError:
            print("Cannot load Nifti object!")

    if len(image.get_data().shape) == 2:
       image = Nifti2Image(np.atleast_3d(image.get_data()), image.affine)
    if len(image.get_data().shape) == 3:
        img = Image3D.Image3D(image=image, color=color_cm)
    elif len(image.get_data().shape) == 4:
        img = Image4D.Image4D(image=image, color=color_cm)
        img.setTime(hdr['pixdim'][4])
    else:
        print ("image error: image is neither 3D nor 4D.")
    if 'sform_code' in image.header.keys():
        img.sform_code = image.header['sform_code']

    # Sets preferences.
    if img.two_cm == True:
        img.presetCMPos(pref['cm_pos'])
        img.presetCMNeg(pref['cm_neg'])
        img.setClippingsPos(pref['clip_pos_low'][0], pref['clip_pos_high'][0])
        img.setClippingsNeg(pref['clip_neg_low'][0], pref['clip_neg_high'][0])
        img.setInterpolation(pref['interpolation'][0])
    else:
        if f_type > 0: # no underlay
            img.presetCMPos(pref['cm_pos'])
            img.setClippingsPos(pref['clip_pos_low'][0], pref['clip_pos_high'][0])
            img.setClippingsNeg(pref['clip_neg_low'][0], pref['clip_neg_high'][0])
            img.setInterpolation(pref['interpolation'][0])
        else:
            img.presetCMPos(pref['cm_under'])
            img.presetCMNeg(pref['cm_neg'])
            img.setClippingsPos(pref['clip_under_low'][0], pref['clip_under_high'][0])
            img.setClippingsNeg(pref['clip_neg_low'][0], pref['clip_neg_high'][0])
            img.setInterpolation(pref['interpolation'][0])

    img.writeProps()

    return img



def loadImageFromFile(filename, pref, f_type):

    color_cm = False
    if f_type != 0:
        color_cm = True

    filetype = os.path.splitext(filename)[1]
    if (filetype=='.nii' or filetype=='.gz'):
        try:
            temp_img = load(filename)
            image = Nifti2Image(temp_img.get_data(), temp_img.affine)
            hdr = temp_img.header
        except RuntimeError:
            print("Cannot load .nii or nii.gz file given!")
    elif (filetype=='.hdr' or filetype=='.img'):
        try:
            temp_img = load(filename)
            image = Nifti2Image(temp_img.get_data(), temp_img.affine)
            image.dataobj[np.isnan(image.dataobj)] = 0
            hdr = temp_img.header
        except RuntimeError:
            print("Cannot load img/hdr pair file given!")

    elif (filetype == '.v'):
        image = load_vista(filename)
        hdr = image.header
        
        #old way of loading vista file!
        # try:
        #     [img_data, dim, pixdim, sform_code, sform, qform_code, qform,
        #         voxel_res, quatern, qoffset, column_vec, row_vec, slice_vec,
        #         index_origin, ca, cp, extent] = pyvista.loadVImage(filename)
        #     hdr = {'pixdim': pixdim}
        #     if len(pixdim) == 1: # version 1 .v file
        #         pixdim.append(voxel_res[1])
        #         pixdim.append(voxel_res[2])
        #         pixdim.append(voxel_res[3])
        #         # Build affine from old version header info
        #         affine = np.eye(4)
        #         affine[0, 0:3] = column_vec
        #         affine[1, 0:3] = row_vec
        #         affine[2, 0:3] = slice_vec
        #         affine[0:3, 3] = np.transpose(index_origin)
        #         # if affine is still build incorrectly, use identity
        #         if np.linalg.det(affine[0:2, 0:2]) == 0:
        #             affine = np.identity(4)
        #         image = Nifti2Image(img_data.astype(np.float32), affine)
        #     else: # version 2 .v file
        #         # sform, or qform, and if not, then fall-back affine
        #         if sform_code != 0:
        #             affine = sform
        #         elif qform_code != 0:
        #             qform_affine = calculateQFormAffine(pixdim, qform_code, qform)
        #             affine = qform_affine
        #         else:
        #             affine = shape_zoom_affine(img_data.shape, pixdim[1:4], False)
        #         image = Nifti2Image(img_data.astype(np.float32), affine)
        #         if sform_code != 0:
        #             image.set_sform(sform)
        #         if qform_code != 0:
        #             qform_affine = calculateQFormAffine(pixdim, qform_code, qform)
        #             image.set_qform(qform_affine)
        # except RuntimeError:
        #     print("Cannot load .v file given!")


    # if data contain NaNs convert to zero
    if np.isnan(image.get_data()).any():
        notnan = image.get_data()
        notnan[np.isnan(image.get_data())] = 0
        image = Nifti2Image(notnan, image.affine)

    # allow 2d-images here:
    if len(image.get_data().shape) == 2:
       image = Nifti2Image(np.atleast_3d(image.get_data()), image.affine)

    if len(image.get_data().shape) == 3:
        img = Image3D.Image3D(image=image, color=color_cm)
    elif len(image.get_data().shape) == 4:
        img = Image4D.Image4D(image=image, color=color_cm)
        frame_time = hdr['pixdim'][4]
        if frame_time > 15:
            frame_time = frame_time/1000
        elif frame_time < 0.015:
            frame_time = frame_time*1000
        img.setTime(frame_time)
    else:
        print ("image error: image is neither 3D nor 4D.")


    if 'sform_code' in hdr.keys():
        img.sform_code = hdr['sform_code']
    
    # Sets preferences.
    if img.two_cm == True:
        img.presetCMPos(pref['cm_pos'])
        img.presetCMNeg(pref['cm_neg'])
        img.setClippingsPos(pref['clip_pos_low'][0], pref['clip_pos_high'][0])
        img.setClippingsNeg(pref['clip_neg_low'][0], pref['clip_neg_high'][0])
        img.setInterpolation(pref['interpolation'][0])
    else:
        if f_type > 0: # no underlay
            img.presetCMPos(pref['cm_pos'])
            img.setClippingsPos(pref['clip_pos_low'][0], pref['clip_pos_high'][0])
            img.setClippingsNeg(pref['clip_neg_low'][0], pref['clip_neg_high'][0])
            img.setInterpolation(pref['interpolation'][0])
        else:
            img.presetCMPos(pref['cm_under'])
            img.presetCMNeg(pref['cm_neg'])
            img.setClippingsPos(pref['clip_under_low'][0], pref['clip_under_high'][0])
            img.setClippingsNeg(pref['clip_neg_low'][0], pref['clip_neg_high'][0])
            img.setInterpolation(pref['interpolation'][0])

    img.writeProps()
    img.filename = filename

    return img
