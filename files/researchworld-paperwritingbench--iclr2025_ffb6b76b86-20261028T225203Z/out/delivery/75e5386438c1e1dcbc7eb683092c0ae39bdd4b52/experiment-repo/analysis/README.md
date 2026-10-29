# Analysis: validity audit of the supplied experimental results

The objective supplies its results (experimental_log.md, quoted in
`/initial-state/inputs/0/INSTRUCTIONS.md`) and forbids reporting anything else as an
experimental result. The large-model runs (7B-13B LMs on FIM, MMLU, ... ) are therefore
not re-run here; this directory checks the supplied numbers, derives the comparisons the
paper's claims rest on, and verifies the synthetic claim that can be checked exactly.

| file | what | from |
|---|---|---|
| `data/table{1..4}_*.csv` | log Tables 1-4, transcribed verbatim | INSTRUCTIONS.md, [EXPERIMENTAL LOGS] §2 |
| `audit.py` -> `derived.json` | all derived differences (pp = absolute percentage points) | `data/*.csv` |
| `markov_check.py` -> `markov_check.out` | exact check of the Figure 2 example | chain drawn in `figures/figure_2.png` |

Reproduce: `python3 audit.py; python3 markov_check.py` (pandas only; <1 s).

## 1. Consistency of figures with the logs
- `figure_6.png` (left table) reproduces log Table 1 exactly (all 10 numbers). Its footnote
  defines **@10 as the maximum pass@10 over a temperature sweep** (right panels,
  temperature 0-1); the paper's setup must say so. The right panels show token-level SPM
  pass@10 stays ~20 pp below PSM at every temperature, while byte-level SPM and PSM overlap.
- `figure_2.png` token-transition labels are correct: Monte Carlo on the tokenized
  stream matches every label within 0.01 (`markov_check.out`, part 1).
- `figure_3.png` (3rd-order chain) shows the biased estimate is 0 for six of eight
  3-byte contexts and the corrected estimate matches ground truth for all eight; this
  agrees with the qualitative log. No numeric values are supplied for it: describe it
  qualitatively only.
- Table 4 beam width 1 equals Table 1 byte-level greedy (65.7 / 63.9): beam width 1 is the
  default byte-level greedy setting, and Table 4's metric is greedy pass rate.

## 2. Claims in the log, checked (C = how the paper may state it)
| log claim | check | C |
|---|---|---|
| "18% improvement ... in SPM mode" | SPM greedy 45.0 -> 63.9 = **+18.9 pp** (42% relative); SPM @10 +17.8 pp | "+18.9 points (greedy) and +17.8 points (@10) in SPM". Do not write "18%" (it is points, not relative). |
| SPM degradation 64.9 -> 45.0 | token PSM->SPM drop 19.9 pp greedy, 17.5 pp @10; byte drop 1.8 pp greedy, -0.2 pp @10 | byte-level recovers 95% of the greedy gap |
| byte > healing, alignment in SPM | greedy +1.2 / +0.9 pp; @10 +0.5 / +1.4 pp | "outperforms, by 0.5-1.4 points"; margins are small, no variance reported |
| byte > token even in PSM | +0.8 pp greedy, +0.1 pp @10 | "slightly higher / comparable"; too small to call a gain without CIs |
| HumanEval ensemble "+3.7%" over best individual | 42.1 vs Yi-Coder token 38.4 = **+3.7 pp**; vs Yi-Coder byte 36.5 = +5.6 pp | state the baseline: "+3.7 points over the best single model (token-level)" |
| MMLU/PIQA/TriviaQA ensemble > best single | +2.0 / +0.6 / +0.6 pp over best token-level; also NQ +1.5 pp | true for 4 of 5 general benchmarks (NQ included) |
| ensemble vs voting | MMLU +3.3 pp, PIQA +0.6 pp; voting equals best member there (62.1, 80.1) | voting only reported on MMLU, PIQA |
| GSM8K: Yi beats Mistral "by 20%" | 61.3 vs 39.0 = **22.3 pp** (byte 61.5 vs 39.0 = 22.5 pp) | "by over 20 points"; ensemble 55.8 is 5.7 pp below Yi byte (61.5) |
| MBPP ensemble | 53.6 = Yi-Coder byte 53.6 (tie, +0.8 pp over its token 52.8) | "matches the best single model"; not a gain |
| beam "up to ~2.9%", "peak 67.7 in PSM" | SPM 63.9 -> 66.8 = +2.9 pp; PSM 65.7 -> 67.7 = +2.0 pp | largest gain is SPM, peak is PSM; monotone in width for both |

## 3. Negative / mixed results the paper must report (not omit)
- **Byte-level vs token-level for single models is not uniformly better**: over the 21
  (model, benchmark) cells of Tables 2-3, byte-level is higher in 7, equal in 4, lower in
  10 (range -3.6 to +1.8 pp; `derived.json` `byte_vs_token_sign_counts`).
- **HumanEval @1 drops for all three code models** under byte-level decoding:
  -3.6 (CodeLlama2-7b), -2.3 (CodeLlama2-13b), -1.9 (Yi-Coder-1.5B) pp.
- Llama2-7B: GSM8K -2.6 pp, NQ -1.6 pp; TriviaQA -0.1 to -0.3 pp for all three models.
- Defensible reading: in the theory the byte-level and token-level models are the same
  distribution, so outside mid-token prompts single-model differences are expected to be
  small and of either sign (decoding with greedy/beam over bytes is not greedy over
  tokens); the method's benefit is concentrated where the prompt ends mid-token (SPM FIM)
  and in enabling cross-vocabulary ensembles. The logs give no cause for the HumanEval
  drops; the paper should say so rather than invent one.
- Ensemble fails when members differ strongly (GSM8K, -5.7 pp vs best member).

## 4. Validity caveats (for the limitations paragraph and review)
- No seeds, repetitions, standard errors or significance tests are reported anywhere.
  Differences below ~1 pp (PSM gains, byte vs healing/alignment, PIQA/TriviaQA ensemble
  gains, Table 2 byte-token differences) should be called comparable, not improvements.
  Planning estimate, not a measurement: a binomial SE of a 65% pass rate is
  100*sqrt(.65*.35/n) pp, i.e. ~3.7 pp at n=164 and ~1.2 pp at n=1640.
- "Top-2" members differ per benchmark (by byte score: MMLU, GSM8K = Yi + Mistral;
  PIQA = Mistral + Yi; NQ, TriviaQA = Mistral + Llama2; HumanEval, MBPP = Yi-Coder +
  CodeLlama2-13b). The log does not state how "top-2" was selected (on test scores?);
  if selected on the test set, ensemble gains are optimistically biased -> limitation.
- Model naming in the log is inconsistent: Table 1 and the setup say "CodeLlama-7b",
  Table 3 says "CodeLlama2-7b" / "CodeLlama2-13b". Use the log's names; do not resolve
  them by outside knowledge, at most note they are as reported.
- FIM results (Tables 1, 4) cover one model (CodeLlama-7b) and one benchmark.
- No runtime/cost numbers are supplied for the reverse search: the paper must not claim
  measured efficiency, only the algorithmic argument.

## 5. Exact check of the Figure 2 example (`markov_check.out`)
Chain with a=0.3, b=0.4, tokenizer with the single merge "AA". For prompts B A^m:
the greedy encoding ends in a lone "A" for odd m, and naive next-token prediction then
gives P(next byte = A) = 0 (truth 1-a = 0.7); summing the same token model over valid
cover encodings gives 0.7 exactly for every m. This verifies the paper's core claim on
the paper's own example; it is a worked illustration (could go to the appendix as a
sanity check), not an experimental result of the study.

## 6. Check of the formal method in paper-repo `template.tex` §3 (draft v2, 4ee06fec8220)
Scripts: `markov_check.py` part 4 (Figure 2 chain) and `method_check.py` (richer MPE and
BPE tokenizers over {a,b,c}, 12 tokens, L=3, random token LM satisfying Assumption 1).
Outputs: `markov_check.out`, `method_check.out`. All pass:
- Algorithm 1 output equals the brute-force Lemma 1 sum over cover encodings;
- the Proposition 1 recursion / Eq. (sampling) equals Algorithm 1 rerun on x_1^{n+1}
  (same encodings, same probabilities) and gives a normalised next-byte distribution;
- on the Figure 2 chain, Eq. (sampling) reproduces the true byte chain (max error 1e-16);
- valid encodings are prefix-closed for both MPE and BPE (all strings up to length 7).
  Proof sketch: MPE, the longest token prefix of a prefix of s is at most the longest
  token prefix of s; BPE, a merge applied in s that lies inside a prefix ending at a
  token boundary is also the highest-priority pair available in that prefix, since pairs
  across the boundary are never merged in s.
- enc(x_1^{n-i}) is *not* a prefix of enc(x_1^n) in about 35% of the histories
  Algorithm 1 visits (139/398 MPE, 129/373 BPE). The histories still share a common
  prefix, but "share most of their prefix" is a practical observation, not a theorem.
Reading of the proofs: Lemma 1 (uniqueness of k, disjointness, pruning) and
Proposition 1 (disjoint split, both inclusions) are correct. Wording points are filed in
paper-repo (see experiment-repo#3).
