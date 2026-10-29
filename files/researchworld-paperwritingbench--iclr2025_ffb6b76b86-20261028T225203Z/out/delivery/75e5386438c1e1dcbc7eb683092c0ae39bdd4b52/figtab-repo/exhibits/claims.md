# Claim → exhibit map, with checks against the experimental log

Numbers are from `data/*.csv` (verbatim from the log, identical to `experiment-repo`
`analysis/data/*.csv`). Differences are in absolute percentage points (pp). Claim IDs follow
story-repo `PLAN.md` §2.

| claim | exhibit | what the reader checks in it |
|---|---|---|
| C1 tokenization bias exists (1st-order chain: P(A after token A)=0 vs 1−α) | `fig:markov1` (figure_2.png) | red edges out of token A: 0.0 to A, 0.0 to AA, 1.0 to B. Matches the log note and `experiment-repo` `analysis/markov_check.py` |
| C2/C3 conversion recovers the byte-level distribution of a trained model | `fig:markov3` (figure_3.png) | green bars ≈ red bars in all 8 contexts. Purple (token-conditioned) ≈ 0 in 6 of 8 (read off the plot: only BAA ≈ 0.77 and AAA ≈ 0.12 are non-zero) |
| method: cover encodings, validity, backward search, sampling | `fig:cover`, `fig:sampling` | schematic. Captions must match the paper's definitions (paper-repo to confirm wording) |
| motivation / ensembling idea | `fig:overview` | schematic; its probabilities are illustrative, not measured |
| C5 mid-token prompts hurt token-level; byte-level fixes it and beats healing/alignment | `fig:fim` (figure_6.png; contains log Table 1) | SPM greedy 45.0 → 63.9 (+18.9 pp) vs healing 62.7, alignment 63.0; SPM @10 66.5 → 84.3 vs 83.8, 82.9; PSM greedy 64.9 → 65.7, @10 84.0 → 84.1. Byte-level is highest in every column. Table numbers in the PNG checked equal to the log |
| C6 byte conversion mostly preserves accuracy, with drops | `tab:general`, `tab:code` | drops visible in place: Llama2-7B NQ 25.0→23.4, GSM8K 15.1→12.5; HumanEval 32.3→28.7, 35.8→33.5, 38.4→36.5 |
| C7 byte-space ensembling of different vocabularies | `tab:general`, `tab:code` | ensemble bold on MMLU 65.4, PIQA 80.7, NQ 30.0, TriviaQA 64.2, HumanEval 42.1; ties on MBPP 53.6; GSM8K 55.8 < 61.5 (not bold, visibly below) |
| C8 beam width helps byte-level FIM | `tab:beam` | PSM 65.7→67.7 (+2.0 pp), SPM 63.9→66.8 (+2.9 pp). Width 1 equals the byte-level greedy numbers of `fig:fim` |

## Wording flags (for text and captions; the authority for numbers is `experiment-repo` `analysis/`)
- "18% improvement" (FIM, SPM) = **+18.9 pp** greedy (45.0→63.9), relative +42%. Write points.
- "up to 3.7%" (HumanEval ensemble) = 42.1 − 38.4 = **+3.7 pp** over the best single model.
- "~2.9%" (beam) = **+2.9 pp in SPM**; PSM gains +2.0 pp. The peak 67.7 is PSM. Do not write
  "2.9% reaching 67.7 in PSM".
- "Yi outperformed Mistral by 20%" on GSM8K = 61.5 − 39.0 = **22.5 pp** byte (22.3 pp token).
- Ensemble members are "the top-2 models" per the log. Members are named in the log only for
  HumanEval (Yi-Coder-1.5B + CodeLlama2-13b) and GSM8K (Yi-1.5-6B + Mistral-7B-v0.3). The table
  captions therefore say "two best-performing models on each benchmark" without naming the others.
- Beam ablation model and decoding are not stated in the log. The `tab:beam` caption only says width 1
  matches the byte-level greedy results of `fig:fim` (65.7 / 63.9), which is checkable.
- `figure_6.png` shows vertical bars for healing/alignment under PSM where the log says N/A. The
  caption says they are evaluated in SPM only.
