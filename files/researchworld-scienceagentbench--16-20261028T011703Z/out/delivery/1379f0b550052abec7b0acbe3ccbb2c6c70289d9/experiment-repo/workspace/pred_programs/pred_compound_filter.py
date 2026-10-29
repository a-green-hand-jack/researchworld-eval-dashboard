"""Filter hit compounds by PAINS/Brenk substructures and similarity to known actives.

A hit is kept when it matches no PAINS (A, B, C) or Brenk filter substructure, and
its maximum Tanimoto similarity to every training compound with ACTIVITY == 1 is
strictly below 0.5 (Morgan fingerprint, radius 2, 2048 bits).
"""

import csv
import os
import sys

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

RDLogger.DisableLog("rdApp.*")

# The task's paths; the environment variables only let the same program run where
# the dataset or the output directory sits elsewhere.
DATA_DIR = os.environ.get("COMPOUND_FILTER_DATA", "/benchmark/datasets/compound_filter")
HITS_PATH = os.path.join(DATA_DIR, "hits.csv")
TRAIN_PATH = os.path.join(DATA_DIR, "train.csv")
OUT_PATH = os.environ.get("COMPOUND_FILTER_OUT", "/workspace/pred_results/compound_filter_results.txt")

SIM_THRESHOLD = 0.5
FP_RADIUS = 2
FP_BITS = 2048


def read_smiles(path, label_column=None, label_value=None):
    """Return SMILES from a CSV; keep only rows whose label matches when given."""
    smiles = []
    # utf-8-sig drops the byte-order mark that hits.csv starts with
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if label_column is not None and row[label_column] != label_value:
                continue
            smiles.append(row["SMILES"].strip())
    return smiles


def build_filter_catalogs():
    pains_params = FilterCatalogParams()
    for catalog in (
        FilterCatalogParams.FilterCatalogs.PAINS_A,
        FilterCatalogParams.FilterCatalogs.PAINS_B,
        FilterCatalogParams.FilterCatalogs.PAINS_C,
    ):
        pains_params.AddCatalog(catalog)
    brenk_params = FilterCatalogParams()
    brenk_params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
    return FilterCatalog(pains_params), FilterCatalog(brenk_params)


def fingerprint(mol):
    return AllChem.GetMorganFingerprintAsBitVect(mol, FP_RADIUS, nBits=FP_BITS)


def main():
    hit_smiles = read_smiles(HITS_PATH)
    active_smiles = read_smiles(TRAIN_PATH, "ACTIVITY", "1")
    print(f"hits read: {len(hit_smiles)}", flush=True)
    print(f"training actives read: {len(active_smiles)}", flush=True)

    pains_catalog, brenk_catalog = build_filter_catalogs()

    active_fps = []
    unparsed_actives = 0
    for smi in active_smiles:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            unparsed_actives += 1
            continue
        active_fps.append(fingerprint(mol))
    print(f"actives parsed: {len(active_fps)} (unparseable: {unparsed_actives})", flush=True)

    unparsed_hits = 0
    after_pains = []
    after_filter = []
    for smi in hit_smiles:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            unparsed_hits += 1
            continue
        if pains_catalog.HasMatch(mol):
            continue
        after_pains.append(smi)
        if brenk_catalog.HasMatch(mol):
            continue
        after_filter.append((smi, mol))
    print(f"hits unparseable (dropped): {unparsed_hits}", flush=True)
    print(f"hits after PAINS: {len(after_pains)}", flush=True)
    print(f"hits after PAINS and Brenk: {len(after_filter)}", flush=True)

    kept_rows = []
    for smi, mol in after_filter:
        sims = DataStructs.BulkTanimotoSimilarity(fingerprint(mol), active_fps)
        if max(sims) < SIM_THRESHOLD:
            kept_rows.append(Chem.MolToSmiles(mol))
    print(f"hits after similarity < {SIM_THRESHOLD}: {len(kept_rows)} kept rows", flush=True)

    # One line per distinct molecule, at its first occurrence in input order
    kept = list(dict.fromkeys(kept_rows))
    print(f"distinct kept molecules: {len(kept)}", flush=True)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as handle:
        for smi in kept:
            handle.write(smi + "\n")
    print(f"wrote {len(kept)} SMILES to {OUT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
