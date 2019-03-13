# Prerequisite software
A list of python libraries are needed for vviewer to function.
You can install them by

  pip install -r requirements.txt


# Setup For Ubuntu 14.04
If you want to start the vviewer directly from the terminal, you will have to edit your ~/.bashrc file, adding this line:

export PATH=<directory>:$PATH

substituting <directory> with the vviewer/vviewer directory (the one that containts vviewer.py).
Then you can launch the viewer as:

vviewer.py -in bla.nii -z overlay.nii

## Setup For Mac
If you don't have pip on your mac, you can install it following these instructions:
https://ahmadawais.com/install-pip-macos-os-x-python/

Alternatively you can use homebrew, macport or get-pip.py from pip's home page.
