# Public data provenance

Sources were downloaded on 2026-10-28 directly from the task-provided fixed revisions. `manifest.json` contains the exact resolved filename/URL, actual byte size, and computed SHA-256 for all four files. Raw files are not in the distribution archive.

| Local file | Source and revision | Declared license | Role |
| --- | --- | --- | --- |
| `raw/arena.csv` | `lmarena-ai/arena-human-preference-55k`, `18c298340948c0e7f7727399fd459cca6ce0ca6f`, `train.csv` | Apache-2.0 | 57,477 crowd preference records |
| `raw/mt_human.parquet` | `lmsys/mt_bench_human_judgments`, `f7d2896d2cc5d80f8b55c2bbc722613555233c25`, human split | CC-BY-4.0 | 3,355 expert/author judgments |
| `raw/mt_gpt4.parquet` | Same MT snapshot, GPT-4 pair split | CC-BY-4.0 | 2,400 released model judgments |
| `raw/nba.csv` | `fivethirtyeight/data`, `4c1ff5e3aef1816ae04af63218015066e186c147`, `nba-elo/nbaallelo.csv` | CC-BY-4.0 | Historical games, deduplicated and season-filtered |

Attribution: Arena and MT data are released by LMSYS/LMArena and the benchmark authors credited in Chiang et al. (2024) and Zheng et al. (2023); historical NBA archive by FiveThirtyEight. License declarations are from the task's verified data catalog. There is no claim that new authors collected these records. No live evaluations or user interventions were performed.

Preprocessing is entirely in `src/prepare.py`:

1. Retain all primary Arena and MT records and all their contestants. Ties become outcome 0.5. GPT-4 `tie (inconsistent)` is 0.5 primarily, then separately removed.
2. Canonicalize model/team ordering and reverse the label when necessary. One published judgment remains one indivisible edit unit. Conversation strings are not model features and are not used for interpreting an attack.
3. NBA: `_iscopy==0`, `is_playoffs==0`, `year_id` in 2013, 2014, 2015, fit each season separately. Team names are original `team_id` values, not historical franchises merged over decades. No supplied Elo values are used. The archive has 63,157 unique games and two rows per game overall; the selected seasons have 1,229, 1,230, and 1,230 games respectively.
4. Human/GPT-4 matching uses question ID, turn, and unordered model-pair keys; choose one actual human annotation per key, uniformly with fixed seed, then merge its GPT-4 counterpart. The 1,814 shared keys have identical row order, model-pair schedule, and cluster assignments across judges.

The supplied expected SHA-256 values for Arena, human MT, and NBA were verified exactly. The GPT-4 file's computed checksum is included even though the task did not supply one. No login was required. Raw data and derived row arrays stay under `data/`, excluded from `submission.zip` and any code repository; the manifest and this provenance file are included.
