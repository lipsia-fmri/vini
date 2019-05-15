"""
Resampling methods to resample the image data.
"""

from multiprocessing import Process
from multiprocessing import sharedctypes
import os
import warnings
import numpy as np
from numpy import ctypeslib
import scipy as sp
from scipy import ndimage, linalg
from distutils.version import LooseVersion, StrictVersion

def resample_image(data, affine, shape, interpolation):

    A = affine[0:3,0:3]
    b = affine[0:3,3]

    # The following is necessary because of an inconsistency in scipy's
    # resampling method for versions < 0.18.0.
    if np.all(np.diag(np.diag(A)) == A):
        if LooseVersion(sp.__version__) < LooseVersion("0.18.0"):
            b = np.dot(np.linalg.inv(A),b)
        A = np.diag(A)

    shape = tuple(np.asarray(shape).astype(int))

    result = np.empty(shape,  dtype=float)
    ndimage.affine_transform(
        data, A, b, output_shape=shape, output=result, order=interpolation)

    return result

if __name__ == "__main__":

    # small test of scipy's ndimage.affine_transform
    A = np.zeros((4,4))
    B = np.zeros((2,2))

    A[1,1] = 1
    A[2,2] = np.nan

    ndimage.affine_transform(A, [1,1], [2,2], (2,2), B, 0)

    print(B)
