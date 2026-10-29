import os, numpy as np
from bt import Data
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(name):
    z = np.load(os.path.join(ROOT, "data", "processed", name + ".npz"), allow_pickle=False)
    return Data(z["a"], z["b"], z["y"], list(z["names"]), z["extra"] if "extra" in z.files else None)
