import os
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

D = "benchmark/datasets/compound_filter/"
hits = pd.read_csv(D + "hits.csv", encoding="utf-8-sig")
train = pd.read_csv(D + "train.csv", encoding="utf-8-sig")
train = train[train["ACTIVITY"] == 1]

params = FilterCatalogParams()
params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
params.AddCatalog(FilterCatalogParams.FilterCatalogs.BRENK)
catalog = FilterCatalog(params)

def fp(m):
    return AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)

active_fps = []
for s in train["SMILES"]:
    m = Chem.MolFromSmiles(s)
    if m is not None:
        active_fps.append(fp(m))

kept = []
for s in hits["SMILES"]:
    m = Chem.MolFromSmiles(s)
    if m is None or catalog.HasMatch(m):
        continue
    if max(DataStructs.BulkTanimotoSimilarity(fp(m), active_fps)) < 0.5:
        kept.append(s)

os.makedirs("pred_results", exist_ok=True)
with open("pred_results/compound_filter_results.txt", "w") as f:
    for s in kept:
        f.write(s + "\n")
print(len(kept))
