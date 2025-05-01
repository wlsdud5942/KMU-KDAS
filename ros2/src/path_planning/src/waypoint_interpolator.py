from scipy.interpolate import splprep, splev
import numpy as np

def interpolate_path(points, num=100):
    x, y = zip(*points)
    tck, u = splprep([x, y], s=0)  
    unew = np.linspace(0, 1, num=num)
    out = splev(unew, tck)
    return list(zip(out[0], out[1]))

  
