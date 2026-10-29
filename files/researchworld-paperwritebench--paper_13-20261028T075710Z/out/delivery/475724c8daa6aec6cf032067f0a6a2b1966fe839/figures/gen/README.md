# Figures and tables: provenance

Regenerate (repo root): `python3 figures/gen/make_tables.py && python3 figures/gen/make_figures.py && python3 figures/gen/fill_task_figure.py` (from the repo root; needs numpy-free matplotlib + Pillow).

| Output | Source | Generator | Change from frozen input |
|---|---|---|---|
| `tables/table_kf.tex` (Task 1) | `inputs/8/table_kf.tex` | `make_tables.py` / `data.py` | grouped by model type, sorted by F1 in group, arrows, caption states the metric/bold convention. Numbers identical. |
| `tables/table_vs.tex` (Task 3) | `inputs/8/table_vs.tex` | same | added signed $\Delta$ row (computed). Caption names the model version-neutrally (source says Qwen2.5-VL-7B but the baseline row equals the Qwen2-VL-7B row of table_kf; paper-repo#4). |
| `tables/table_xj.tex` | `inputs/8/table_xj.tex` | same | `\cmidrule` fix, arrow semantics in caption, bold computed (ours in 12/12 cells), caveat that metrics are only comparable within an encoder. |
| `tables/table_zn.tex` | `inputs/8/table_zn.tex` | same | diffs recomputed from counts: step-6 class change is -962 (source printed -982, arithmetically wrong). |
| `tables/table_os.tex` | `inputs/8/table_os.tex` | same | column alignment, note that #samples of ours = bboxes (6,925 images). Cite keys unchanged. |
| `figures/fig_task1_recall.pdf` | table_kf | `make_figures.py` | new: R@1/3/5 + F1 per model (shows the CLIP-vs-LMM rank flip between R@1 and R@5). |
| `figures/fig_task3_menu_effect.pdf` | table_vs | `make_figures.py` | new: paired with/without-description change per metric. |
| `figures/ACM_task.jpg` | `inputs/4/ACM_task.jpg` | `fill_task_figure.py` | text written into 4 empty boxes + "Class names" label; unmodified copy: `figures/ACM_task_original.jpg`. Labels inferred from the overview text; owner of report to confirm. |
| other `figures/*.jpg` | `inputs/4/*.jpg` | (copied) | none. Underlying data not supplied, so not re-rendered. |
