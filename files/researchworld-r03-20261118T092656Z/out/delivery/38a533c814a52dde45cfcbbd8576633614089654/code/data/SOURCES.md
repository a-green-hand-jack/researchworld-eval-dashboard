# Generative-LLM score matrices: sources and notes
Retrieval date: 2026-11-18. Raw downloads live in /hutian/data/{olmb,helm_lite,livebench,dense}/ (outside the repo).
Build scripts: /hutian/repo/src/build_*.py, fetch_olmb_results.py (run with `python3 -I script args`).
Licence caveat: for the HF datasets below the dataset cards state NO licence field; "licence" gives what is stated at the source.

## 1. olmb_matrix.parquet  (Open LLM Leaderboard v2 "contents")
- URL: https://huggingface.co/datasets/open-llm-leaderboard/contents ; commit 9c09a7cae43334062a82cb164f2ef255013dafa2 (data/train-00000-of-00001.parquet, 1.1 MB)
- Licence/terms: none stated on dataset card (no `license:` in YAML). The leaderboard Space is tagged apache-2.0. Per-model licences are in column `license` (Hub License; 1753 empty).
- Shape: 4576 rows x 42 cols; 6 benchmarks. Score missingness: 0.0 (no NaN in any score).
- Columns used: `{ifeval,bbh,math_lvl5,gpqa,musr,mmlu_pro}_norm` = leaderboard normalized scores (0-100; the "IFEval","BBH","MATH Lvl 5","GPQA","MUSR","MMLU-PRO" columns), `*_raw` = the "... Raw" columns (0-1), `average_norm` = "Average".
- Metadata kept: model_id (=fullname), eval_name (unique key; id+precision), type/type_icon, precision, weight_type, architecture, model_sha, license, hub_likes, params_b, moe, flagged, merged, official_provider, generation, chat_template, co2_kg, submission_date (12 NaT), upload_date (530 NaT), base_model_raw/base_model ("(Merge)" suffix stripped; "Removed"/"" -> NaN, 571 rows), base_org, org (prefix of fullname), family_group (= base_model, else model_id; 3851 groups; for family-held-out splits), family_heur (coarse keyword backbone family: llama/qwen/mistral/gemma/phi/...; 2000 rows = "other"; heuristic, verify before use).
- Caveats: model_id is NOT unique (4497 unique; 158 rows / 79 ids duplicated across bfloat16/float16 or different sha, flag `dup_model_id`); eval_name is unique. Flagged=True for 1 row only; Merged=True for 715 rows (type "base merges and moerges" 1724). Many rows are fine-tunes/merges of the same base (strong family correlation); submission_date range 2024-06-08..2025-03-13 (narrow; upload_date goes back to 2022). Scores are for the HF-hosted open models only (no closed models).

## 2. helm_lite_matrix.parquet  (HELM Lite v1.13.0)
- URL: https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/v1.13.0/ (groups/core_scenarios.json "Accuracy" table, schema.json for model metadata); release date 2025-01-10.
- Licence/terms: none stated in bucket; HELM code repo stanford-crfm/helm is Apache-2.0.
- Shape: 91 models x 10 scenarios (+ helm_mean_win_rate, + metadata creator_organization, access, release_date 2022-01-01..2024-12-24, num_parameters, model_run_name). Missingness: 1/910 = 0.11% (Phi-3 (7B) has no GSM8K).
- Metrics (columns): narrativeqa_f1 (NarrativeQA F1), naturalquestions_openbook_f1 (NQ open-book F1), naturalquestions_closedbook_f1 (NQ closed-book F1), openbookqa_em, mmlu_em, math_equiv_cot (MATH Equivalent (CoT)), gsm8k_em, legalbench_em, medqa_em, wmt14_bleu4 (WMT 2014 BLEU-4). All 0-1.
- Caveats: scenario scores are means over the scenario's run specs (e.g. MMLU = mean of 5 subjects, LegalBench = 5 subtasks run in HELM Lite, MATH = 7 subjects); display names unique, no duplicates, all matched to schema metadata. Includes closed API models. `helm_mean_win_rate` is derived from the other columns -- exclude when predicting.

## 3. livebench_matrix.parquet and livebench_category_matrix.parquet  (LiveBench model_judgment)
- URL: https://huggingface.co/datasets/livebench/model_judgment ; commit 9704e5da7bfbefe75ac1482a13de827127295993 (data/leaderboard-00000-of-00001.parquet)
- Licence/terms: none on dataset card (arXiv 2406.19314); GitHub LiveBench/LiveBench licence detection = NOASSERTION.
- IMPORTANT: this pinned snapshot contains only 60,372 judgements covering 195 models x **7 tasks** in **3 categories** (coding: LCB_generation, coding_completion; instruction_following: paraphrase, story_generation; language: typos, plot_unscrambling, connections), not the full 18 tasks / 6 categories. Only 26-100 questions per task.
- Task matrix: 195 models x 7 tasks; column per task = mean score (0-1) over questions (re-judgements of the same (question,model) -- 984 duplicate rows -- averaged first), `nq_<task>` = number of questions, plus n_tasks, n_questions_total, first/last_tstamp. Missingness 23.3% (only 37 models have all 7 tasks, 157 have >=6; models/task coverage 97-182). Some model-task cells rest on few questions (n_questions_total min 4) -- filter on nq_* if needed.
- Category matrix: 195 x 3 (coding/instruction_following/language), `_qmean` (question-weighted) and `_taskmacro` (mean of task means) and `nq_*`; missingness 11.3%.
- Caveats: model names are LiveBench model strings (not normalized; e.g. "Meta-Llama-3.1-70B-Instruct-Turbo" vs "...-HF" variants separate); no dates besides judgment timestamps; includes closed API models; all turn==1.

## 4. Dense candidates
Evaluated: (a) HELM MMLU v1.13.0, (b) Open LLM Leaderboard v2 per-subtask `results`, (c) BigCodeBench.
### 4a. llm_dense_matrix.parquet = HELM MMLU 57 subjects (primary, clean licence; closed + open models)
- URL: https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/groups/mmlu_subjects.json ("Accuracy" table; schema.json for metadata). Release 2025-01-10.
- Licence/terms: none stated in bucket; HELM repo Apache-2.0.
- Shape: 79 models x 57 subject columns `mmlu_<subject>_em` (exact match, 0-1, 5-shot HELM MMLU) + `mmlu_all_subjects_em` (aggregate, exclude when predicting) + metadata (creator_organization, access, release_date 2023-02-26..2024-12-24, num_parameters, model_run_name). Missingness 0.0.
- Caveats: subject test sets are small (100 questions for several subjects => noisy, scores quantised to 0.01); 79 models are mixed API/open, many near ceiling.
### 4b. llm_dense_olmb_subtasks.parquet = Open LLM Leaderboard v2 per-subtask (larger; same models as olmb_matrix)
- URL: https://huggingface.co/datasets/open-llm-leaderboard/results ; commit aa81ecc38fdc5708254b833923368970efdf5ef5 (lastModified 2025-03-15); latest `results_*.json` per model directory (4508 models; 10509 files in repo; ~512 MB raw, not in repo).
- Licence/terms: NO README/licence on dataset at that commit (not stated); treat as unclear -- check before redistribution.
- Shape: 4508 models x 40 leaf benchmarks (24 BBH subtasks `bbh_*` acc_norm; 3 GPQA `gpqa_{diamond,extended,main}` acc_norm; 3 MuSR acc_norm; 7 MATH-Hard subjects `math_*_hard` exact_match; IFEval `ifeval_prompt_strict_acc` and `ifeval_inst_strict_acc`; `mmlu_pro_acc` single aggregate -- the 14 MMLU-Pro categories are NOT in these files). All raw 0-1 (NOT normalized-for-chance like olmb_matrix). Missingness 0.025% (5 models with NaN). Plus metadata joined from olmb_matrix (family_group, base_model, org, family_heur, submission_date, params_b, merged, flagged, ...; `in_contents` False for 11 models that are absent from the contents table; `n_contents_rows`>1 for duplicate ids).
- Caveats: the "latest file" per model may differ from the run used in `contents` (multiple results files per model, e.g. re-runs 2025-02-13); duplicate-precision variants collapse to one model dir; same family-correlation caveats as olmb_matrix; the ifeval pair and the 3 GPQA / 7 MATH sets are highly related sub-benchmarks.
### 4c. BigCodeBench (rejected)
- https://github.com/bigcode-project/bigcodebench @ 09dd993f46c3fbf3a799465bb96d524edcb0b199 (Apache-2.0). That commit holds code only (analysis/get_results.py, task2domain.json); model results live on the HF leaderboard/other repos and per-model scores are by problem (1140 tasks) or a handful of aggregates, so no ready model x >=30 benchmark matrix; not pursued.
