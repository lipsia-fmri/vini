# -*- coding: utf-8 -*-
"""
vista loader, native python implementation
"""

import scipy.io as sio
import numpy as np
import subprocess
import nibabel as nib
import re


#%%writer
# dtype = np.int16
# # data_orig = 13*np.ones((6,6,6), dtype=dtype)
# xdim = 2
# ydim = 5
# zdim = 4
# # tdim = 11

# data_1D = np.arange(xdim*ydim*zdim, dtype=np.int32)
# data_orig = np.reshape(data_1D, (xdim, ydim, zdim))

# # data_1D = np.arange(xdim*ydim*zdim*tdim, dtype=dtype)
# # data_orig = np.reshape(data_1D, (xdim, ydim, zdim, tdim))


# nii_orig = nib.Nifti1Image(data_orig, np.eye(4))
# nii_orig.to_filename("/home/morty/tmp/test.nii")
# subprocess.call("vnifti -in /home/morty/tmp/test.nii -out /home/morty/tmp/test.v", shell=True)

# #%%BINARY writer
# dtype = np.int16
# # data_orig = 13*np.ones((6,6,6), dtype=dtype)
# xdim = 5
# ydim = 5
# zdim = 5
# # tdim = 11

# data_1D = np.ones(xdim*ydim*zdim, dtype=np.int32)
# data_1D = np.random.rand(xdim*ydim*zdim)
# data_1D[data_1D>0.5] = 1
# data_1D[data_1D<=0.5] = 0
# # data_1D = np.zeros(xdim*ydim*zdim)
# # data_1D[4] = 1



# data_orig = np.reshape(data_1D, (xdim, ydim, zdim))

# nii_orig = nib.Nifti1Image(data_orig, np.eye(4))
# nii_orig.to_filename("/home/morty/tmp/test.nii")
# subprocess.call("vnifti -in /home/morty/tmp/test.nii -out /home/morty/tmp/testa.v", shell=True)
# subprocess.call("vbinarize -in /home/morty/tmp/testa.v -out /home/morty/tmp/test.v -min 0.5", shell=True)


#%% AUX
def get_property_str(header_img, str_property, repn_property="int"):
    if header_img is None:
        return -1
    idx_begin = header_img.find(str_property)
    if idx_begin == -1:
        return -1
    idx_val = idx_begin + len(str_property) + 2  
    value = header_img[idx_val:].split('\n')[0]
    if repn_property == "int":
        value = int(value)
    elif repn_property == "str":
        pass
    elif repn_property == "float":
        value = float(value)
    elif repn_property == "list":
        value = value[1:-1].split(" ")
        value = [float(l) for l in value]
    return value

def get_subheader(header, section_demark):
    idx_start = header.find(section_demark)
    if idx_start == -1:
        return
    idx_stop = -1
    for j in range(idx_start, idx_start+5000):
        if header[j] == "}":
            idx_stop = j+1
            break
    return header[idx_start:idx_stop]
    
    
#%% reader
# fp_input = "/mnt/50tbd/gabriele/median_02.v"

def load_vista(fp_input):
    
    with open(fp_input, 'rb') as f:
        raw=f.read()
    
    #find the ^L breaker, determining where the header part stops
    for i in range(len(raw)):
        if raw[i:i+2]==b'\x0c\n':
            last_idx_header = i+2
            break
    
    #now parse the header for the first time to load the data.
    header = raw[0:last_idx_header-2].decode("utf-8")
    
    #find all proper images and parse each of them into dict. store all dicts in list_images
    list_imagedict = []
    idx_images = [m.start() for m in re.finditer(': image {', header)]
    
    #blacklist some images
    idx_images = [l for l in idx_images if header[l-5:l]!="sform"]
    
    for i in range(len(idx_images)):
        dict_image = {}
        dict_image['idx_header_begin'] = idx_images[i]
        #find end of image definition in header
        for j in range(idx_images[i], idx_images[i]+5000):
            if header[j] == "}":
                dict_image['idx_header_end'] = j+1
                break
            
        header_img = header[dict_image['idx_header_begin']:dict_image['idx_header_end']]    
        dict_image["repn"] = get_property_str(header_img, "repn", "str")
        dict_image["offset"] = get_property_str(header_img, "data", "int") + last_idx_header
        dict_image["length"] = get_property_str(header_img, "length", "int")
        
        dict_image["nbands"] = get_property_str(header_img, "nbands", "int")
        if dict_image["nbands"] == -1:
            dict_image["nbands"]  = 1
        
        
        dict_image["nrows"] = get_property_str(header_img, "nrows", "int")
        dict_image["ncolumns"] = get_property_str(header_img, "ncolumns", "int")
        tr = get_property_str(header_img, "repetition_time", "float")
        
        if tr > 0:
            dict_image["repetition_time"] = tr
        
        #fix dtype
        if dict_image["repn"] == "int":
            dict_image["dtype"] = np.int32
            dict_image["length"] = int(dict_image["length"]/4)
        elif dict_image["repn"] == "long":
            dict_image["dtype"] = np.int64
            dict_image["length"] = int(dict_image["length"]/8)
        elif dict_image["repn"] == "float":
            dict_image["dtype"] = np.float32
            dict_image["length"] = int(dict_image["length"]/4)
        elif dict_image["repn"] == "double":
            dict_image["dtype"] = np.float64
            dict_image["length"] = int(dict_image["length"]/8)
        elif dict_image["repn"] == "short":
            dict_image["dtype"] = np.int16
            dict_image["length"] = int(dict_image["length"]/2)
        elif dict_image["repn"] == "bit":
            dict_image["dtype"] = np.int16
            dict_image["length"] = int(dict_image["length"]/1)
        elif dict_image["repn"] == "ubyte":
            dict_image["dtype"] = np.uint8
            dict_image["length"] = int(dict_image["length"]/1)
            
        else:
            raise ValueError("Read error: data representation '{}' unknown. please contact support.".format(dict_image["repn"]))
            
        list_imagedict.append(dict_image)
        
        
    #decide: was the image 3D or 4D (time series)
    if len(list_imagedict) == 1: #<=3D case
        dict_image = list_imagedict[0]
        xdim = dict_image["ncolumns"]
        ydim = dict_image["nrows"]
        zdim = dict_image["nbands"]
        tdim = 1
        
        if dict_image["repn"] != "bit": #default case
            img1D = np.frombuffer(raw, dtype=dict_image["dtype"], count=dict_image["length"], offset=dict_image["offset"]).byteswap()
        else: #bit representation (masks etc)
            img1D_byterepn = np.frombuffer(raw, dtype=np.uint8, count=dict_image["length"], offset=dict_image["offset"])#.byteswap()
            img1D_bit_graced = np.array([])
            for l in img1D_byterepn:
                bx = bin(l)[2:]
                bx = (8-len(bx))*"0"+bx
                for j in range(8):
                    # b = bx[7-j]
                    b = bx[j]
                    img1D_bit_graced = np.append(img1D_bit_graced, int(b))
            img1D = img1D_bit_graced[0:xdim*ydim*zdim]
            
        img3D = np.transpose(np.reshape(img1D, (zdim,ydim,xdim)), (2,1,0))
        data = img3D
        dim = "3D"
    else:
        list_images = []
        for i in range(len(idx_images)):
            dict_image = list_imagedict[i]
            list_images.append(np.frombuffer(raw, dtype=dict_image["dtype"], count=dict_image["length"], offset=dict_image["offset"]).byteswap())
        if dict_image["repn"] == "bit":
            raise ValueError("bit reprensetation not allowed for 4D images!")
        #concatenate, form a long 1D vector
        xdim = dict_image["ncolumns"]
        ydim = dict_image["nrows"]
        tdim = dict_image["nbands"]
        zdim = len(list_images)
        img1D = np.zeros(xdim*ydim*zdim*tdim, dtype=dict_image["dtype"])
        for i in range(len(idx_images)):
            img1D[i*xdim*ydim*tdim:(i+1)*xdim*ydim*tdim] = list_images[i]
        img4D = np.transpose(np.reshape(img1D, (zdim,tdim,ydim,xdim)), (3,2,0,1))
        data = img4D
        dim = "4D"
        
        
    #%% re-parse the header to get the complete header information
    nii_loaded = nib.Nifti1Image(data, affine=np.eye(4))
    mm = get_property_str(header_img, "voxel", "list")
    if dim == "4D":
        mm.append(tdim)
    nii_loaded.header.set_zooms(mm)
    nii_loaded.header['pixdim'][4] = tr
    nii_loaded.header.set_xyzt_units(xyz="mm", t="msec")
    

    
    #get s-form code
    sform_code = get_property_str(header, "sform_code", "int")
    if sform_code != -1:
        nii_loaded.header['sform_code'] = sform_code
    qform_code = get_property_str(header, "qform_code", "int")
    if qform_code != -1:
        nii_loaded.header['qform_code'] = qform_code
    
    header_sform = get_subheader(header, "sform: image")
    offset_sform = get_property_str(header_sform, "data", "int")
    if offset_sform != -1:
        offset_sform += last_idx_header
        length_sform = int(get_property_str(header_sform, "length", "int")/4)
        sform1D = np.frombuffer(raw, dtype=np.float32, count=length_sform, offset=offset_sform).byteswap()
        sform2D = np.reshape(sform1D, (4,4))
        nii_loaded.set_sform(sform2D)
    
    
    header_dim = get_subheader(header, "dim: bundle")
    offset_dim = get_property_str(header_dim, "data", "int")
    if offset_sform != -1:
        offset_sform += last_idx_header
        length_dim = int(get_property_str(header_dim, "length", "int")/4)
        dim1D = np.frombuffer(raw, dtype=np.float32, count=length_dim, offset=offset_dim)
        
    
    header_pixdim = get_subheader(header, "pixdim: bundle")
    offset_pixdim= get_property_str(header_dim, "data", "int")
    if offset_sform != -1:
        offset_sform += last_idx_header
        length_pixdim = int(get_property_str(header_dim, "length", "int")/4)
        pixdim1D = np.frombuffer(raw, dtype=np.float32, count=length_dim, offset=offset_dim)
        
        
    header_qform = get_subheader(header, "qform: bundle")
    offset_qform = get_property_str(header_qform, "data", "int")
    if offset_sform != -1:
        offset_sform += last_idx_header
        length_qform = int(get_property_str(header_qform, "length", "int")/4)
        qformdim1D = np.frombuffer(raw, dtype=np.float32, count=length_qform, offset=offset_qform)
        nii_loaded.header['quatern_b'] = qformdim1D[0]
        nii_loaded.header['quatern_c'] = qformdim1D[1]
        nii_loaded.header['quatern_d'] = qformdim1D[2]
        nii_loaded.header['qoffset_x'] = qformdim1D[3]
        nii_loaded.header['qoffset_y'] = qformdim1D[4]
        nii_loaded.header['qoffset_z'] = qformdim1D[5]
        # quatern_b quatern_c quatern_d qoffset_x qoffset_y qoffset_z
    
    
    
    return nii_loaded

# nii_loaded.to_filename("/home/morty/tmp/out.nii")
