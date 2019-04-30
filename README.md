![viff_main](https://github.com/lipsia-fmri/viff/blob/master/docs/viff.png)
**viff** is a light-weight viewer for MR data. The strives to be fast and simple, yet powerful. Viff also features many practical keyboard shortcuts.


Currently, the following file formats are supported:
*.nii,

*.nii.gz,

*.img/.hdr and

*.v (lipsia's vista format)

*.npy (numpy arrays on disk)

The viewer is written in python and does not have any external dependencies.

# Installation
Install as python package via pip:

        pip3 install git+https://github.com/lipsia-fmri/viff.git


# Upgrading
Upgrading the already installed viff viewer works as follows:

        pip3 install git+https://github.com/lipsia-fmri/viff.git --upgrade

# How-to

## Open an image
You can open images directly from the terminal, using

        viff -in data.nii

Alternatively, you can click in the menu on file / open image or hit "o".


## Clicking and slicing
![viff_vox](https://github.com/lipsia-fmri/viff/blob/master/docs/viff_vox.png)

You can click and drag into any of the panes to navigate within the each of the three panes. You can use the arrow keys on your keyboard for voxel-by-voxel steering (the green crosshair indicates the active pane).
In order to zoom into the image, use your mouse wheel or "CTRL and +" or "CTRL and -" on your keyboard.
If you want to pan the image left, right, up or down, hold the mouse wheel button while moving.
The voxel's current location is displayed in the **(A)**, in voxel coordinates. If you want to switch to millimetres/MNI coordinates, click on the button **(B)**. The intensity value of the current image at the crosshair's position is shown **(C)**.

## Multiple images and overlay
![viff_main](https://github.com/lipsia-fmri/viff/blob/master/docs/viff_multi.png)
You can overlay multiple images on top of each others. Add another image by clicking the button **(A)**. Remove them with **(B)**. The order of images can be changed with the buttons **(C)**, the most top image is drawn on top all other ones, overlaying whatever is below. If you want to turn an image invisible, click on the checkmark **(D)** next to the image name. 

## Colormaps
### Basics
![viff_color](https://github.com/lipsia-fmri/viff/blob/master/docs/viff_color.png)
Intensity value are displayed by virtue of a  *colormap*, which assigns a color to the given values. By default, we use a gray-scale colormap **(A)**, assigning black to the smallest value in your image and white to the largest, everything in between will be a shade of gray. You can change the colormap and select another one by clicking on the colormap. We have a selection of colormaps ready to select. Note that the color for the maximum value is displayed on the right side of the color bar, while the minimum is shown on the left.
You can change the *lower* threshold for the colormap with the slider **(B)**. Changing the position of the right handle changes the lower threshold (the one closer to 0), the current value is shown in **(C)**. The *higher* threshold can be changed with the handle **(D)** and the according value is displayed at **(E)**. For information on how image values outside the specified range are displayed, see *Clipping behaviour* below.


### Two color maps
Some situations require that you want to have two color maps for the same image. For instance, if you want to display positive and negative values with different colors. You can activate a second color bar for such situations, just press "i" or go to image/image settings. This will bring up the image menu. There, select "color maps" and "two color maps".
Alternatively, you can open the image directly with the *-z* flag:

        viff -z data.nii


The second color map is independent of the first one and has its own slider with maximum and minimum handle. They are shown to the right of the first one.

### Clipping behaviour
What happens if the image values are outside the range of the color map assignment? Per default, values *above* the upper limit are shown in the same color as the maximum. Values *below* the lower limit are however not drawn and thus invisible. We call the latter procedure *clipping*, meaning that colors are just clipped away. You can change the default behaviour in the image settings menu (press "i") or image/image settings. There, for each active colorbar you find two checkboxes for clipping. By default, the "clip upper threshold" for the positive colorbar is disabled (meaning that values above are just shown with the maximum color) and "clip lower threshold" is enabled (making them invisible if below).


## Histogram
You can show the histogram of values for the currently selected image via tools/histogram or by pressing "h". On the x-axis, you will find the given image values, on the y axis the count. The section of image values that is within the selected colormap is shown in blue, meaning that if you pull the colormap handles, this box will shift. You can however also directly interact with this box, resulting in changes in the colormap. You can also move around the whole range by dragging the blue box.  This can be useful for looking for a band of image values (with enabling clipping on both sides).

## Time series data
![viff_time](https://github.com/lipsia-fmri/viff/blob/master/docs/viff_time.png)
The viewer is able to load time series data. If time series data is detected, the time series are becomes visible. The number box **(A)** shows the currently selected time volume, here you can enter a number to jump to the volume directly. The horizontal slider **(B)** shows the position in the overall time series. You can drag it to show the time series data at any given point. If you want to move in time in a more controlled fashion, you can click the buttons **(C)** to just move one volume back, to play the time series as movie, and to go volume forward. The same can be achieved by pressing "n" and "b" (next and before) and "space" for starting/stopping the movie. The play button **(D)** plays back the time series as movie, the same can be achieved by pressing "Space" on your keyboard.

## Maximum and minimum
You can jump to the local maximum or minimum of the selected image. For this, click on the buttons **(e)**. The search radius can be changed in the preferences.



# Advanced stuff

## Mosaicing
You can create a mosaic view of the currently selected images and thresholds. For this, click on Tools/Open Mosaic Dialogue or hit "m". You can determine the grid of the mosaic by setting the numbers of rows and columns, which determines the number of slices. The starting frame and end frame set the slice end points. If the slices are perfectly divisible the *increment* field shown on the bottom will be in bold. Having the increment in bold ensures that the slice distance is the same within the mosaic. Hit "slice to mosaic" to render it. Note that in the mosaic you will still be able to zoom and pan.

## bring window out. link views

## linked views

## Resampling options
Images usually come with affine transformations (saved in the header), that encode a translation and rotation. You can disable the resampling and sample to the next closest voxel resolution by clicking on Resampling/Ignore affine and pray.



# Keyboard shortcut cheat sheet
* o: open file
* cursor left,right,up,down: change crosshair position within selected pane (green one!)
* page up/down: change voxel position in remaining dimension (orthogonal to the selected plane)
* h: histogram
* m: mosaic dialogue
* v: toggle image visibility
* space: start/stop playing movie for time series
* n/b: move to next or previous frame in time series
* w/s: select the image above or below
