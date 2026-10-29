"""Filter hit compounds: drop PAINS/Brenk matches and compounds whose maximum
Tanimoto similarity (Morgan radius 2, 2048 bits) to any active training
compound is >= 0.5. Kept SMILES are written one per line."""
import os

import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

RDLogger.DisableLog("rdApp.*")

DATA_DIR = "/benchmark/datasets/compound_filter"
# <workspace>/pred_results, i.e. /workspace/pred_results in the task environment
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(WORKSPACE, "pred_results", "compound_filter_results.txt")
THRESHOLD = 0.5


GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def fingerprint(mol):
    return GENERATOR.GetFingerprint(mol)


def main():
    hits = pd.read_csv(os.path.join(DATA_DIR, "hits.csv"), encoding="utf-8-sig")
    train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"), encoding="utf-8-sig")

    params = FilterCatalogParams()
    for cat in (FilterCatalogParams.FilterCatalogs.PAINS,
                FilterCatalogParams.FilterCatalogs.BRENK):
        params.AddCatalog(cat)
    catalog = FilterCatalog(params)

    active_fps = []
    for smi in train.loc[train["ACTIVITY"] == 1, "SMILES"]:
        mol = Chem.MolFromSmiles(smi)
        if mol is not None:
            active_fps.append(fingerprint(mol))

    kept = []
    for smi in hits["SMILES"]:
        mol = Chem.MolFromSmiles(smi)
        if mol is None or catalog.HasMatch(mol):
            continue
        sims = DataStructs.BulkTanimotoSimilarity(fingerprint(mol), active_fps)
        if max(sims, default=0.0) < THRESHOLD:
            kept.append(smi)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write("\n".join(kept) + ("\n" if kept else ""))
    print(f"{len(kept)} of {len(hits)} compounds kept -> {OUT_PATH}")


if __name__ == "__main__":
    main()
