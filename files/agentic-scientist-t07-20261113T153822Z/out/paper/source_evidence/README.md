# Readable source evidence

- `selected_method.py`: byte-for-byte copy of the delivered source under the registry's selected-configuration directory, `results/ideas/03_rasch_residual_profile_mixtures_on_fixed_score_targeted_prefixes/program_1/src/program.py`.
- `METHOD.md`: accompanying implementation notes, used as context and checked against readable code rather than treated as empirical evidence.
- `program_spec.toml`: original entrypoint manifest.
- `evaluate_final.py`: supplied final evaluator. Its file hash agrees with `paper_data.json.final_evaluation.evaluator_sha256`.
- `final_data_manifest.json`: staged data/grouping manifest copied from `task/resources/final/manifest.json`.

The files support source-level descriptions; they do not establish which fitted hyperparameters were selected or certify that every execution path passed structural checks. Use final evaluator records for measured results and qualification. The final evaluation did not qualify, and the unknown underlying causes of missing records remain unknown.

These snapshots were inspected, not executed during manuscript preparation. Their original source files remain available through the supplied task/results links in this environment. Moving the evaluator snapshot alone does not move its relative resource dependencies; see the reproduction instructions before any future independent evaluation.
