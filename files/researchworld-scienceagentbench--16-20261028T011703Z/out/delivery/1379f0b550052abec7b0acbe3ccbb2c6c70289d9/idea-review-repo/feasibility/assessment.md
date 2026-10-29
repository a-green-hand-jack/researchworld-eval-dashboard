# Feasibility assessment: compound filter study

Source of facts: `/initial-state/inputs/1/benchmark/datasets/compound_filter/` (`hits.csv`, `train.csv`), sandbox checks made this turn. Working material; not a delivered path.

## Measured

| Item | Value | Source |
|---|---|---|
| hits.csv compounds | 3640 | `wc -l`, header excluded |
| train.csv rows | 39311 | `wc -l` = 39312 incl. header |
| train actives (`ACTIVITY=1`) | 512 | `grep -c ',1$'` |
| train inactives (`ACTIVITY=0`) | 38800 | `grep -c ',0$'` |
| train rows unlabelled | 0 | `grep -vc ',[01]$'` |
| train.csv header | BOM before `SMILES` | first bytes |
| RDKit in `/hutian/.venv` | absent | import failed |
| RDKit on research network | rdkit 2026.9.1 resolves | `pip install --dry-run rdkit` |
| CPUs / memory | 2 CPUs; 4 GB sandbox limit | `nproc`, sandbox spec |

## Planning estimates

- Compute: PAINS and Brenk catalogue matching on 3640 compounds plus Tanimoto of 3640 × 512 fingerprints is seconds of CPU. No resource job is needed.
- Installation: a single RDKit install, expected to be quick once the network is reachable.

## Risks

1. Fingerprint not specified by the request; results depend on it. The plan must fix and state it.
2. "Maximum Tanimoto < 0.5 to any active" is read as max over the 512 actives < 0.5. Confirm.
3. SMILES parse failures need a stated rule (drop and count).
4. Stereo and salt/standardisation handling must be stated.
5. Inactives must not be used as references.
6. RDKit version must be recorded with the delivery.

## Verdict

Feasible at the stated scale. No blocker is known. The open items are method choices, not resource limits.

## Settled method (story-repo, `plan/study-plan.md` at 0aa8a72)

Morgan radius 2, 2048 bits, chirality off; similarity to all 512 actives, keep only if max < 0.5 (strict); unparseable SMILES dropped and counted; `utf-8-sig` for `train.csv`; PAINS (A, B, C) and BRENK via RDKit `FilterCatalog`; output canonical SMILES in input order.

Feasibility review of the settled method: no conflict with the measured facts or risks above. Remaining checks at delivery: RDKit version recorded, parse-failure count and per-filter drop counts present in the run log, output count matches the run log, and the program runs in the sandbox without a background job.

Minor point, not a blocker: the request says "save the SMILES representations", and the plan writes canonical SMILES. This is a reasonable reading, and it should be stated in the delivered report or run log.
