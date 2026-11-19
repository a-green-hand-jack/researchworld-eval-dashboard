"""Download the nine ppi-python 0.2.3 example datasets into ../data (Google Drive via gdown, no account needed)."""
import os
from ppi_py.datasets import load_dataset
os.makedirs("../data", exist_ok=True)
for n in ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare",
          "census_education", "plankton", "ballots"]:
    d = load_dataset("../data/", n); print(n, {k: v.shape for k, v in d.items()})
