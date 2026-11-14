import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for rel in ("../src", "../scripts"):
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, rel)))
os.environ.setdefault("OMP_NUM_THREADS", "1")
