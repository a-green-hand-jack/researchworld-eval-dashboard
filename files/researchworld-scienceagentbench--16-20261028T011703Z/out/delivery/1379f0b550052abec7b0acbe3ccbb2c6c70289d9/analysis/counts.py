"""Counts and sensitivity checks for the compound filter (run record for REPORT.md).

Usage: python3 analysis/counts.py <data_dir>
Reads hits.csv and train.csv from data_dir and prints every number used in REPORT.md.
"""
import csv
import sys
from collections import Counter

from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

RDLogger.DisableLog("rdApp.*")
data = sys.argv[1]


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def catalog(*names):
    p = FilterCatalogParams()
    for n in names:
        p.AddCatalog(getattr(FilterCatalogParams.FilterCatalogs, n))
    return FilterCatalog(p)


hits = [r["SMILES"] for r in read(data + "/hits.csv")]
train = read(data + "/train.csv")
actives = [r["SMILES"] for r in train if r["ACTIVITY"] == "1"]
print(f"train rows {len(train)}; actives (ACTIVITY == 1) {len(actives)}; inactives {len(train) - len(actives)}")
print(f"hits rows {len(hits)}; distinct raw SMILES {len(set(hits))}")

hit_mols = [Chem.MolFromSmiles(s) for s in hits]
print(f"unparseable hits {sum(m is None for m in hit_mols)}")
act_mols = [Chem.MolFromSmiles(s) for s in actives]
print(f"unparseable actives {sum(m is None for m in act_mols)}")

pains = catalog("PAINS_A", "PAINS_B", "PAINS_C")
brenk = catalog("BRENK")
p = [pains.HasMatch(m) for m in hit_mols]
b = [brenk.HasMatch(m) for m in hit_mols]
n = len(hits)
print(f"PAINS alone {sum(p)}; Brenk alone {sum(b)}; both {sum(x and y for x, y in zip(p, b))}; union {sum(x or y for x, y in zip(p, b))}")
print(f"after PAINS {n - sum(p)}; after PAINS and Brenk {n - sum(x or y for x, y in zip(p, b))}")


def kept_rows(radius=2, bits=2048, thr=0.5, use_fp="morgan"):
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=bits)
    afp = [gen.GetFingerprint(m) for m in act_mols if m is not None]
    out = []
    for smi, m, pp, bb in zip(hits, hit_mols, p, b):
        if pp or bb or m is None:
            continue
        sim = max(DataStructs.BulkTanimotoSimilarity(gen.GetFingerprint(m), afp))
        if sim < thr:
            out.append((smi, Chem.MolToSmiles(m)))
    return out


kept = kept_rows()
base = [canon for _, canon in kept]
print(f"kept rows {len(base)}; distinct canonical molecules {len(set(base))}")
dup = Counter(base)
print("repeated canonical molecules:", sum(1 for v in dup.values() if v > 1), "; surplus lines:", sum(v - 1 for v in dup.values() if v > 1))
raw_kept = [raw for raw, _ in kept]
print(f"kept rows as raw input strings: {len(raw_kept)}; distinct raw strings {len(set(raw_kept))}")

print("sensitivity (kept rows / distinct canonical molecules):")
for radius in (1, 2, 3):
    for thr in (0.4, 0.5, 0.6):
        k = [canon for _, canon in kept_rows(radius=radius, thr=thr)]
        print(f"  radius {radius}, threshold {thr}: {len(k)} / {len(set(k))}")
for bits in (1024, 4096):
    k = [canon for _, canon in kept_rows(bits=bits)]
    print(f"  bits {bits}, radius 2, threshold 0.5: {len(k)} / {len(set(k))}")

# Inactives: the filter uses actives only. Count the kept set if a hit close to any inactive is also dropped.
inact = [r["SMILES"] for r in train if r["ACTIVITY"] == "0"]
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
inact_fps = [gen.GetFingerprint(m) for m in (Chem.MolFromSmiles(s) for s in inact) if m is not None]
with_inact = 0
for _, canon in kept:
    m = Chem.MolFromSmiles(canon)
    if max(DataStructs.BulkTanimotoSimilarity(gen.GetFingerprint(m), inact_fps)) >= 0.5:
        with_inact += 1
print(f"kept rows that also have an inactive at similarity >= 0.5: {with_inact}")
print(f"kept rows if a hit with an inactive at similarity >= 0.5 is also dropped: {len(kept) - with_inact}")

# Canonicalisation: raw strings that merge into one kept molecule.
by_canon = {}
for raw, canon in kept:
    by_canon.setdefault(canon, []).append(raw)
print("merged raw strings (canonical -> raw strings), for molecules with more than one raw string:")
for canon, raws in by_canon.items():
    if len(set(raws)) > 1:
        for raw in sorted(set(raws)):
            print(f"  {canon}\t{raw}")
