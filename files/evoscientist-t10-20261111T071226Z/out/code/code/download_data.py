"""Downloads the nine ppi-python example collections (v0.2.3) into ./data/ (via gdown, from Google Drive)."""
import os
from ppi_py.datasets import load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data") + os.sep
os.makedirs(DATA, exist_ok=True)
for n in ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare",
          "census_education", "plankton", "ballots"]:
    d = load_dataset(DATA, n)
    print(n, {k: d[k].shape for k in d.files})
