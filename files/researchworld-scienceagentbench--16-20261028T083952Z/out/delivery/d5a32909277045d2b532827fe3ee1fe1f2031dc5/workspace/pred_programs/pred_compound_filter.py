"""Filter the compounds in hits.csv and save the SMILES of those kept.

A compound is kept when it has no PAINS (A, B, C) or Brenk substructure
match and its maximum Tanimoto similarity to the active compounds of
train.csv (ACTIVITY == 1) is strictly below 0.5. Each distinct surviving
SMILES is written once, in first-occurrence order.
"""

import csv
import os
import sys

from rdkit import Chem, DataStructs, __version__ as rdkit_version
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

DATA_DIR = "/benchmark/datasets/compound_filter"
HITS_PATH = os.path.join(DATA_DIR, "hits.csv")
TRAIN_PATH = os.path.join(DATA_DIR, "train.csv")
OUT_DIR = os.environ.get("PRED_RESULTS_DIR", "/workspace/pred_results")
OUT_PATH = os.path.join(OUT_DIR, "compound_filter_results.txt")

SIM_THRESHOLD = 0.5
FP_RADIUS = 2
FP_BITS = 2048


def read_rows(path):
    # utf-8-sig drops the byte-order mark the files start with
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def make_filter_catalog():
    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_A)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_B)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_C)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
    return FilterCatalog(params)


MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=FP_RADIUS, fpSize=FP_BITS)


def fingerprint(mol):
    return MORGAN.GetFingerprint(mol)


def main():
    hits = read_rows(HITS_PATH)
    train = read_rows(TRAIN_PATH)
    counts = {"input": len(hits)}

    # Parse the hits and keep only valid SMILES
    parsed = []
    for row in hits:
        mol = Chem.MolFromSmiles(row["SMILES"].strip())
        if mol is not None:
            parsed.append((row["SMILES"].strip(), mol))
    counts["valid_smiles"] = len(parsed)

    catalog = make_filter_catalog()
    no_alert = []
    for smiles, mol in parsed:
        if not catalog.HasMatch(mol):
            no_alert.append((smiles, mol))
    counts["after_pains_brenk"] = len(no_alert)

    # Fingerprints of the active training compounds
    active_fps = []
    unparsed_train = 0
    for row in train:
        mol = Chem.MolFromSmiles(row["SMILES"].strip())
        if mol is None:
            unparsed_train += 1
            print("Skipped unparseable training SMILES:", row["SMILES"].strip())
            continue
        if row["ACTIVITY"].strip() == "1":
            active_fps.append(fingerprint(mol))
    counts["active_training"] = len(active_fps)
    counts["unparsed_training"] = unparsed_train

    kept = []
    for smiles, mol in no_alert:
        sims = DataStructs.BulkTanimotoSimilarity(fingerprint(mol), active_fps)
        if max(sims) < SIM_THRESHOLD and smiles not in kept:
            kept.append(smiles)
    counts["after_similarity"] = len(kept)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        for smiles in kept:
            handle.write(smiles + "\n")

    print("RDKit version:", rdkit_version)
    print("Python version:", sys.version.split()[0])
    for stage, n in counts.items():
        print(f"{stage}: {n}")
    print("Wrote", len(kept), "SMILES to", OUT_PATH)


if __name__ == "__main__":
    main()
