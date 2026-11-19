"""Download the ppi-python example datasets (v0.2.3) into ./data/."""
from ppi_py.datasets import load_dataset

NAMES = ["galaxies", "forest", "alphafold", "gene_expression", "census_income",
         "census_healthcare", "census_education", "plankton", "ballots"]
if __name__ == "__main__":
    for n in NAMES:
        try:
            d = load_dataset("./data/", n)
            print(n, {k: getattr(v, "shape", None) for k, v in d.items()})
        except Exception as e:  # noqa
            print("FAIL", n, repr(e)[:200])
