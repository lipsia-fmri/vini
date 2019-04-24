import pyqtgraph_viff  as pg
import numpy as np

app = mkQApp()

def test_nan_image():
    img = np.ones((10,10))
    img[0,0] = np.nan
    v = image(img)
    v.imageItem.getHistogram()
    app.processEvents()
    v.window().close()
