"""Filter hit compounds: drop PAINS / Brenk matches and anything with Tanimoto >= 0.5
to any active training compound; write remaining SMILES, one per line.

Usage: python pred_compound_filter.py [DATA_DIR] [OUT_DIR]
Defaults: /benchmark/datasets/compound_filter  and  /workspace/pred_results
"""
import os
import sys

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

RDLogger.DisableLog("rdApp.*")

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "/benchmark/datasets/compound_filter"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "/workspace/pred_results"
SIM_THRESHOLD = 0.5
FP_RADIUS, FP_BITS = 2, 2048


def fingerprint(mol):
    return AllChem.GetMorganFingerprintAsBitVect(mol, FP_RADIUS, nBits=FP_BITS)


def main():
    hits = pd.read_csv(os.path.join(DATA_DIR, "hits.csv"), encoding="utf-8-sig")
    train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"), encoding="utf-8-sig")

    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
    catalog = FilterCatalog(params)

    actives = train[train["ACTIVITY"] == 1]["SMILES"]
    active_fps = []
    for smi in actives:
        mol = Chem.MolFromSmiles(smi)
        if mol is not None:
            active_fps.append(fingerprint(mol))
    print(f"actives: {len(active_fps)} / {len(actives)} parsed")

    kept, n_invalid, n_alert, n_similar = [], 0, 0, 0
    for smi in hits["SMILES"]:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            n_invalid += 1
            continue
        if catalog.HasMatch(mol):
            n_alert += 1
            continue
        sims = DataStructs.BulkTanimotoSimilarity(fingerprint(mol), active_fps)
        if max(sims) >= SIM_THRESHOLD:
            n_similar += 1
            continue
        kept.append(smi)

    print(f"hits: {len(hits)}, invalid: {n_invalid}, PAINS/Brenk: {n_alert}, "
          f"similar to active: {n_similar}, kept: {len(kept)}")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "compound_filter_results.txt"), "w") as f:
        for smi in kept:
            f.write(smi + "\n")


if __name__ == "__main__":
    main()
