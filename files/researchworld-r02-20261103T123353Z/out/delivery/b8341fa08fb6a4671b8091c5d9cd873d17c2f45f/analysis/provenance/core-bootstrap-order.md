# Archival core bootstrap ordering

Analysis-owned answer to experiment-repo#16, 2026-11-03. This records the actual archival aggregation, not a new estimator, selected repeat subset or scientific rerun.

`analysis/postprocess/core_snapshot.py` SHA-256 is `5bf0da324cdac240d711c3b61e784597ec7df3b8068afef10cd97b6c3187daf4`, identical to `results/core_interim/metadata.json`'s recorded exporter hash. Its outer loop follows the frozen config's ten core cells; the inner loop is numeric `range(100)`. It appends each checkpoint's `saved['rows']` unchanged. The exact emitted checkpoint order is retained in that metadata's `checkpoint_manifest` list. The core cells are interior K3/K10, heterogeneous K3/K10, boundary K3/K10, Dirichlet K3/K10 and zeros K3/K10, in that order. Within any cell/method/group subset, repeats therefore occur 0,1,2,...,99.

Final `scripts/finalize_confirmatory.sh` instead traverses shard0 then shard1 and `sorted(checkpoints.glob('*.json'))`, so within a cell it visits lexical filenames: 0,1,10,11,...,19,2,20,...,99. All underlying scientific rows are the same. This ordering difference does not select or discard any trial.

The pinned `scripts/summarize.py:interval` removes nonfinite values and uses `default_rng(90210).choice(x, size=(5000,n), replace=True).mean(1)` followed by quantiles [.025,.975]. The fixed random indices act on ordered x. Reordering x leaves the theoretical bootstrap distribution unchanged, but changes a finite realized 5000-draw endpoint. Means/SD/t intervals agree up to roundoff; unpaired bootstrap endpoints need not. Paired summaries use `pivot(index='repeat',...)`, whose repeat index is sorted, so their ordering is already consistent across these exports.

To verify historical core bootstrap columns from fresh complete trial rows, assign each `(cell,repeat)` the index of its matching checkpoint in the original manifest, retain every core trial and **stable-sort by that index**, preserving within-checkpoint method/group row order. Run the unchanged pinned summarizer and study_summaries.py on those rows. This reproduces the original summary, component, group-denominator and component-minus-joint bootstrap calculations, plus their derived exports. Do not compare historical core unpaired bootstrap endpoints directly with final-aggregation endpoints or omit those uncertainty columns. Keep final-export endpoints checked under their own original order and preserve every displayed t interval, scientific field, case and decision flag. Fresh timing fields may differ by machine and remain outside scientific equivalence, as specified by presentation's verifier.

The exact mapping is based on manifest list position; parsing a manifest filename uses `Path(entry['path']).stem.rsplit('__',1)` to recover cell and integer repeat. No new fit, calibration, test draw or statistical policy is introduced. The verification helper is outside scripts/ to preserve the frozen runner's source inventory.

Measured replay in `core-bootstrap-check.json` passed: all 2,050 summary entries, 442 component summaries, 370 paired summaries and every derived export (238 denominator/fit entries, 442 component-minus-joint gaps, 216 coverage-gap entries, 64 minimum-group entries and 10 bootstrap-sensitivity entries) match the original numeric values exactly after parsing, including all bootstrap columns. The empty cross-cell-sensitivity file is preserved as empty. This check uses the complete retained canonical trial rows reordered by the manifest; it creates no new scientific trial. The receipt records the initial checker-only empty-CSV parsing error and the successful corrected check.

From the delivery root, independently replay the check into a new output directory with:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 analysis/postprocess/verify_archival_core.py --input analysis/results/confirmatory/trials.jsonl --output analysis/results/core_order_verification
```

The helper's default reference is the retained archival `analysis/results/core_interim/`; `--core` selects an equivalent copy containing its metadata and summary/derived exports. It reuses the pinned summarizer and derived-summary implementation and checks their retained source hashes. This is an analysis-owned provenance check; presentation's fresh-result gate remains its own supported interface.
