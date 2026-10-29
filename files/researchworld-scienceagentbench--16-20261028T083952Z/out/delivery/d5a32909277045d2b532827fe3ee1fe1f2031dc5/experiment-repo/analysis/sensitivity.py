import csv, sys
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator as G
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
RDLogger.DisableLog("rdApp.*")
D="/benchmark/datasets/compound_filter"
rd=lambda p:list(csv.DictReader(open(p,newline="",encoding="utf-8-sig")))
hits=rd(f"{D}/hits.csv"); train=rd(f"{D}/train.csv")
p=FilterCatalogParams()
for c in ["PAINS_A","PAINS_B","PAINS_C","BRENK"]: p.AddCatalog(getattr(FilterCatalogParams.FilterCatalogs,c))
cat=FilterCatalog(p)
mols=[(h["SMILES"].strip(),Chem.MolFromSmiles(h["SMILES"].strip())) for h in hits]
clean=[(s,m) for s,m in mols if not cat.HasMatch(m)]
act=[Chem.MolFromSmiles(t["SMILES"].strip()) for t in train if t["ACTIVITY"].strip()=="1"]
act=[m for m in act if m is not None]
print("pains+brenk removed:", len(mols)-len(clean), "remaining:", len(clean))
def run(name,gen,thr=0.5):
    afp=[gen.GetFingerprint(m) for m in act]
    kept=[s for s,m in clean if max(DataStructs.BulkTanimotoSimilarity(gen.GetFingerprint(m),afp))<thr]
    print(f"{name:28s} thr={thr}: kept={len(kept)} distinct={len(set(kept))}")
    return kept
base=run("morgan r2 2048",G.GetMorganGenerator(radius=2,fpSize=2048))
run("morgan r1 2048",G.GetMorganGenerator(radius=1,fpSize=2048))
run("morgan r3 2048",G.GetMorganGenerator(radius=3,fpSize=2048))
run("fcfp r2",G.GetMorganGenerator(radius=2,fpSize=2048,atomInvariantsGenerator=G.GetMorganFeatureAtomInvGen()))
run("atompair 2048",G.GetAtomPairGenerator(fpSize=2048))
for t in (0.45,0.55):
    run("morgan r2 2048",G.GetMorganGenerator(radius=2,fpSize=2048),t)
