# Objective and venue requirements, one line each, with owner and check

Source: `Research objective` issue (#1) and `/initial-state/inputs/0/{TASK,deliverable,data,resources}.md`.
"Path" is the proposed delivered path; the names are fixed only by `.forgejo/CODEOWNERS` of
`paper-repo` (main, 28e314a): `code/`, `results/`, `README.md` experiment-repo; `paper/figures/`, `paper/tables/` figtab-repo; `paper/neurips_2026.sty` venue-repo; `paper/checklist.tex` paper-repo and venue-repo; `venue/` venue-repo; the rest of `paper/` paper-repo. Owner names the position whose work satisfies it.

| ID | Requirement | Owner | Proposed path | Check |
|---|---|---|---|---|
| R1 | Paper as PDF **and** LaTeX source, NeurIPS 2026 template | paper-repo | `paper/main.pdf` (name to be confirmed by paper-repo), `paper/main.tex`, `paper/neurips_2026.sty` (byte copy of `venue/neurips_2026.sty`) | `venue/check_venue.py paper main README.md paper.pdf` |
| R2 | Main text <= 9 content pages | paper-repo (figtab-repo for figure size) | | checker |
| R3 | Paper contains abstract, intro, related work, method, experiments, discussion and limitations, references | paper-repo | | checker |
| R4 | Completed NeurIPS checklist inside the PDF | paper-repo (answers), venue-repo (template) | `paper/checklist.tex` (copy of `venue/checklist.tex`, answers by paper-repo, venue-repo reviews) | checker |
| R5 | Anonymous submission mode, no acknowledgments | paper-repo | | checker (WARN heuristics) |
| R6 | Code, reproduction notes: environment and dependency versions, data acquisition and data version, seeds, run commands, expected runtime | experiment-repo (PLAN.md assigns `README.md` to it) | `README.md`, `code/`, `results/` | checker `REPRO` argument (keyword heuristic) |
| R7 | Each table and figure mapped to the script that produces it | figtab-repo / experiment-repo | in the reproduction notes | read by internal-review-repo |
| R8 | Every number, table, figure from rerunnable code; failed or unfinished runs reported as such | experiment-repo, paper-repo | | internal-review-repo |
| R9 | Only real, consulted references | paper-repo, idea-repo | `paper/references.bib` | internal-review-repo spot checks |
| R10 | Forbidden-content rule: do not seek the published paper on this problem or anything citing/discussing it; record any accidental encounter (what, where, how much read) in the reproduction notes, even if "none" | all positions; notes by paper-repo | `README.md`, section "Forbidden-content log" | every position reports to experiment-repo/paper-repo; checker looks for the section |
| R11 | Uncertainty reporting (repeated runs, intervals), empirical coverage at nominal 95%, mean width comparison; conditions with and without gain | story-repo/experiment-repo/figtab-repo | | not a venue matter; recorded as the objective's standard |
| R12 | Datasets: `ppi-python==0.2.3` data (tag `v0.2.3`, commit `6b8475b`) or others, with licence stated (npz files have no separate licence declaration) | idea-repo / experiment-repo | | repro notes |
| R13 | Budget limits: CPU only, <5 GB storage, one-week limit | all | | experiment-repo |

Venue-only files supplied here (copy unchanged into the paper directory):
`venue/neurips_2026.sty`, `venue/checklist.tex` (blank template with its question texts),
`venue/paper_skeleton.tex` (section order and package set), `venue/check_venue.py`.
