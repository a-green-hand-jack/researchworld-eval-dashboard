# figtab-repo

Presentation position: figures and tables of the paper.

- `figures/scripts/` plotting/table scripts; each reads the tidy CSVs of `experiment-repo/results` (schema: `notes/result_schema_request.md`)
  and writes PDF+PNG (+ `.settings.txt` caption text) to `out/`. Run e.g. `python3 code/fig_main.py --results <dir> --out out --width 5.5`.
- `dev/mock_fixture.py` (run `python3 dev/mock_fixture.py <dir>`) writes RANDOM tables with the schema, only to smoke-test the layout. Its outputs carry no result and are never delivered.
- Delivered figures/tables go to `paper-repo` (`figures/`, `tables/`) by pull request once real results exist.
