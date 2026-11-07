# Validation at the delivered analysis path

The report owner requested `analysis/**`; the merged paper CODEOWNERS assigns that entire directory to experiment-repo. The package preserves this repository's structure under `analysis/`, including pinned requirements, acquisition/provenance, scripts, measured results, exact attack witnesses, methods/claim map and the presentation evidence interface. Raw input files and ignored matched per-replicate directories are excluded.

Checked in a fresh paper checkout with this directory structure:

- `analysis/scripts/check_methods.py`: independent optimizer, orientation invariance, infinitesimal influence and duplication/penalty-scaling checks pass at lambda .1/1/10 without raw data.
- `analysis/scripts/summarize.py`: regenerates all primary/robustness and consolidated matched summaries without ignored directories or raw downloads; paired estimates agree with archived outputs to floating-point precision (below 1e-12).
- `analysis/scripts/verify_witnesses.py`: using the pinned raw input directory at `analysis/data`, reconstructs every primary attack and checks the recorded exact-refit margin; all pass. The temporary input-directory link used for this test was removed and is not delivered.

The README explicitly instructs `cd analysis` in the delivered root, documents installation and all run commands, and distinguishes archive-only summary generation from full reproduction. `notes/presentation_inputs.md` maps each supplied figure/table claim to its numerical artifact and producing analysis script; final rendering scripts belong to figtab-repo under `presentation/`.

No experiment was rerun for these packaging changes; only the numerical validity checks, result reconstruction and summary derivation were executed. Full study limitations and the post-hoc selection control remain documented.
