# Reproduction scope

This release supports arithmetic replay of every plotted measurement and table in `paper.tex` from `paper_data.json`. It also preserves inspectable selection and data-preparation sources. Replay is not a fresh evaluation, a new data download, or a claim that the isolated original execution environment has been independently reconstructed. No new scientific experiment was run during manuscript production.

## Environment and commands

Original declared numerical dependencies are in `source_evidence/requirements.txt`: NumPy 2.2.6, SciPy 1.15.3, and Matplotlib 3.10.3. Use Python 3.12. The actual writing/replay tools are pinned separately in `paper_tools_requirements.txt`; Pillow supports the orchestrator-owned concept placeholder. Install additional tools in a private directory outside the manuscript workspace.

```sh
python3 -m venv /tmp/ranking-paper-env
/tmp/ranking-paper-env/bin/pip install -r paper_tools_requirements.txt
/tmp/ranking-paper-env/bin/python build_figures.py
/tmp/ranking-paper-env/bin/python replay_checks.py
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
```

Replay and plotting require no network, GPU, data downloads, or paid APIs. Their runtime is not offered as a benchmark. The supplied seed evaluations took about 29.6–30.5 seconds each, including their surrounding evaluation work, not just method computation (`paper_data.json`, final episode durations). Full isolated re-execution requires the original public task/harness environment and should not be confused with the commands above. The current release does not advertise a self-contained substitute for that external environment.

## Output map

- Figure 1: `figures/sensitivity_overview.png`, orchestrator-owned `generate-concept-figure` output. `build_figures.py` creates only a guarded placeholder and empty prompt log until orchestration; it never replaces a completed render.
- Figure 2: `build_figures.py` → `figures/final_disruption_comparison.pdf` and `.png`, derived directly from final episode curves.
- Figure 3: `build_figures.py` → `figures/paired_effect_uncertainty.pdf` and `.png`, stored endpoints without fabricated centers.
- Table 1: `build_figures.py` → `panel_table.tex`, embedded verbatim in `paper.tex`.
- Supplementary table: `build_figures.py` → `seed_table.tex`, embedded verbatim in `paper.tex`.
- `derived_summary.json` contains the descriptive means; `replay_report.json` checks coefficients, inversion fractions, percentile endpoints, nesting lengths/uniqueness, control records, and weighting arithmetic. Sidecars record source trails.

The immutable measurement source is `paper_data.json.final_evaluation`, not development scores or candidate self-reports. Seeds are 401, 503, and 607. The public contract fixes control streams at seed + 8371, degree matching at seed + 72831, and grouped bootstrap at seed + 49207; the final protocol uses eight random streams and thirty resamples. These settings are documentary protocol facts in `source_evidence/task_contract.json`, not new measurements.

## Data acquisition and reconstruction

Do not redistribute raw conversation data with the paper. Store raw sources under a working `data/` directory outside version control. The two pinned sources and expected SHA-256 values are:

| Source | Snapshot | Expected SHA-256 |
| --- | --- | --- |
| Arena `train.csv`, Apache-2.0 | `18c298340948c0e7f7727399fd459cca6ce0ca6f` | `0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2` |
| FiveThirtyEight `nbaallelo.csv`, CC-BY-4.0 | `4c1ff5e3aef1816ae04af63218015066e186c147` | `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc` |

```sh
mkdir -p data
curl -L 'https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv' -o data/train.csv
curl -L 'https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv' -o data/nbaallelo.csv
python source_evidence/prepare_data.py --arena data/train.csv --nba data/nbaallelo.csv
```

Preparation verifies expected checksums and writes normalized panels alongside the preparation source in `source_evidence/resources/`. This command is supplied for reconstruction; it was not rerun during writing. `source_evidence/panel_manifest.json` is a copy of the existing final manifest, not a fresh checksum verification. Inspect `source_evidence/prepare_data.py` for reciprocal NBA checks, Arena content grouping, partition rules, and exclusions. Neither conversation provenance nor dependence is reconstructed from anonymous candidate rows.

## Selection and evaluation boundary

`source_evidence/flip_search.py` is a byte-preserving copy of the retained selected source; `source_evidence/entrypoint.toml` records its original loader contract. It exports `handle(request)` and is not a command-line benchmark. Its inline finite-array protocol is documented at the top of the file. `source_evidence/task_contract.json` specifies the objective, controls, grouped resampling, failure handling, and external limits. `source_evidence/source_manifest.json` records source identity, inspection locations, and the frozen final tree digest without pretending that the digest is implementation evidence or an independently verified equivalence proof.

`reproduction_task/` additionally distributes unmodified original task preparation, capture and evaluation sources, with a copy manifest and without raw panels. These files were copied for code availability, not executed or used as newly inspected implementation evidence in this writing step. Their original callable entrypoints require the original harness/transport environment; do not assume that invoking them directly substitutes for that environment. The inspected selected source and public contract, rather than opaque metadata or copied-but-unread files, support manuscript implementation descriptions.

No component ablations, penalty sweep, selection-aware bootstrap, deletion experiments, or matched human/judge comparisons are asserted. Guided fixed-panel curves repeat across seeds; this is not independent data replication. Final qualification completed successfully as recorded in `final.qualification.*`, independently of the absence of a downstream study record; it is not a publication or superiority decision.

## Literature, independence, template, and assistance

The bibliography replaces unrelated automated retrieval records with direct identified methodological originals and explicitly permitted seed literature. `references_provenance.json` records retrieval identifiers and reading scope. Supplementary access failures are documented honestly; no full-text reading is claimed when only an original abstract was consulted. No broad leaderboard-attack search, citation expansion, or attempt to identify the restricted paper was made. No known restricted content was encountered in this writing step. Metadata-only records are not used to assert uninspected technical results.

The ICLR 2026 official style was retrieved from the ICLR Master-Template repository's `iclr2026/` directory. URLs and content hashes are in `source_evidence/template_provenance.json`. Review mode preserves the official anonymous author block; author identities, affiliations, funding and acknowledgements are omitted. This paper does not imply acceptance at ICLR. Significant LLM assistance is disclosed in the manuscript's separate `LLM Usage` subsection.

Evidence verification uses `.codex/skills/scientific-evidence/scripts/scientific_evidence.sh`; claim, reference, figure-schema and rendered-PDF checks are performed separately. Passing link validation proves connected provenance, not the truth of every scientific interpretation.
