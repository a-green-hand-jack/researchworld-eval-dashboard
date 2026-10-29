import os
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

RDLogger.DisableLog("rdApp.*")

DATA_DIR = "/workspace/benchmark/datasets/compound_filter"
OUT_PATH = "/workspace/pred_results/compound_filter_results.txt"
SIM_CUTOFF = 0.5

hits = pd.read_csv(os.path.join(DATA_DIR, "hits.csv"))
train = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
actives = train[train["ACTIVITY"] == 1]

params = FilterCatalogParams()
params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
catalog = FilterCatalog(params)


def fingerprint(mol):
    return AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)


active_fps = []
for smi in actives["SMILES"]:
    mol = Chem.MolFromSmiles(smi)
    if mol is not None:
        active_fps.append(fingerprint(mol))

kept = []
for smi in hits["SMILES"]:
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        continue
    if catalog.HasMatch(mol):
        continue
    sims = DataStructs.BulkTanimotoSimilarity(fingerprint(mol), active_fps)
    if max(sims, default=0.0) < SIM_CUTOFF:
        kept.append(smi)

with open(OUT_PATH, "w") as f:
    f.write("\n".join(kept) + "\n")
print(f"Kept {len(kept)} of {len(hits)} compounds -> {OUT_PATH}")
