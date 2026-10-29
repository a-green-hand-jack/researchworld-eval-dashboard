# Claim ledger for the experimental log

Source: `[EXPERIMENTAL LOGS]` in `/initial-state/inputs/0/INSTRUCTIONS.md` (T1-T4 = Tables 1-4 there); figure content read from `/initial-state/inputs/2/figure_{2,3,6}.png`.
Recomputation: `analysis/ledger.py` -> `results/*.csv` (all differences in **percentage points** unless "rel."). No new measurements; no number below is new, only differences of log numbers.
Status: **S** supported as stated; **Q** supported with the qualification/rewording given; **N** not supported as stated (do not write it).
"Report wording" is what `paper-repo` may state. Hard rules: say "points" for absolute differences; no significance claims; do not state benchmark sizes, shot counts, hyperparameters, hardware, compute cost or decoding details that the log does not give.

## A. FIM (T1, Fig. 6)
| # | Log claim | Recomputed | St. | Report wording |
|---|---|---|---|---|
| A1 | Standard token-level drops from PSM to SPM (64.9 -> 45.0 greedy) | -19.9 pts greedy; @10 84.0 -> 66.5 = -17.5 pts | S | "drops by 19.9 points (greedy) and 17.5 points (@10)". The log's reason (mid-token prompts in SPM) is an interpretation; Fig. 2 mechanism supports it, but the log has no ablation isolating it: write "consistent with". |
| A2 | Byte-level recovers SPM greedy to 63.9, comparable to PSM | byte PSM 65.7 vs SPM 63.9: gap 1.8 pts (token gap 19.9) | Q | "narrows the PSM-SPM gap from 19.9 to 1.8 points"; not "closes". |
| A3 | "18% improvement in SPM vs standard token baseline" | greedy +18.9 pts (= +42.0% rel.); @10 +17.8 pts (= +26.8% rel.) | **N as "18%"** / Q | "+18.9 points (greedy) and +17.8 points (@10) in SPM mode". Do not write "18% improvement" unqualified (nor "18% relative"). |
| A4 | Byte-level consistently outperforms healing and alignment (SPM) | greedy: +1.2 (healing 62.7), +0.9 (alignment 63.0); @10: +0.5 (83.8), +1.4 (82.9). Same sign in 4/4 cells | Q | "higher in all four comparisons, by 0.5-1.4 points". Single run, no CI/paired test: margins are small, do not say "significantly" or "clearly". Healing and alignment are SPM only (N/A in PSM). |
| A5 | "Unexpected" PSM greedy gain 65.7 vs 64.9 | +0.8 pts; PSM @10 +0.1 pts | Q | "on par / marginally higher (+0.8 greedy, +0.1 @10)"; no claim of a real improvement. |
| A6 | Fig. 6 caption: "across all settings the byte-level predictions yield better completions" | 4/4 cells higher than token-level, and than healing/alignment where present; smallest margin +0.1 (PSM @10) | Q | Say "highest in all four columns" (true by the numbers), not "better" with an implication of significance. |
| A7 | (Fig. 6 note, not in the log text) "@10 here is the max over the temperature sweep" | read from `figure_6.png` | S | State this when defining @10 in the report if @10 is described. The log's own text gives no sampling settings; do not add any beyond this note. Greedy corresponds to temperature 0.00 in the figure's x-axis start, but the log does not say so: write only "greedy". |
| A8 | Specific error cases ("delimeter", "collatz", "palindrome") | qualitative, no numbers | S (qualitative) | Describe as illustrative examples; no frequency claim. |

## B. General LMs (T2) and ensembling
| # | Log claim | Recomputed | St. | Report wording |
|---|---|---|---|---|
| B1 | Byte-level conversion preserves single-model performance (implicit; T2) | byte-token within +-0.3 pts in 13/15 cells; exceptions Llama2-7B NQ -1.6 (25.0->23.4), GSM8K -2.6 (15.1->12.5) | Q | "matches token-level within 0.3 points in 13 of 15 model-benchmark cells; lower for Llama2-7B on NQ (-1.6) and GSM8K (-2.6)". Byte is *not* uniformly >= token. Largest positive: MMLU Llama2 +0.3, PIQA Mistral +0.2, NQ Mistral +0.3, GSM8K Yi +0.2. |
| B2 | Byte-level top-2 ensemble generally outperforms member models | vs best byte member: MMLU +2.0 (65.4 vs 63.4 Yi), PIQA +0.4 (80.7 vs 80.3), NQ +1.2 (30.0 vs 28.8), TriviaQA +0.7 (64.2 vs 63.5), GSM8K **-5.7** (55.8 vs 61.5). vs best token member: +2.0/+0.6/+1.5/+0.6/-5.5 | Q | "improves over the best single model on MMLU, PIQA, NQ and TriviaQA (by 0.4-2.0 points) but not on GSM8K". Only MMLU gain is more than ~1 point; PIQA/TriviaQA gains are tiny. |
| B3 | Voting baseline (top-2) is weaker than the ensemble | MMLU voting 62.1 vs ens 65.4 (+3.3); PIQA 80.1 vs 80.7 (+0.6). Voting is N/A for NQ, TriviaQA, GSM8K | S (2 benchmarks only) | Compare on MMLU and PIQA only. Note voting (62.1 MMLU) is below the best member Yi 63.4: voting did not even match the best single model there; the log does not say how ties/top-2 are resolved: do not describe the voting procedure beyond "top-2 voting". |
| B4 | Ensemble hurts when members diverge in capability (GSM8K) | Yi 61.5 vs Mistral 39.0 (byte): gap 22.5 pts (token 22.3); relative 58% of Mistral; ensemble 55.8 = -5.7 vs Yi, +16.8 vs Mistral | Q | The log's "by 20%" matches neither gap in points (22.5) nor relative terms: write "by about 22 points". The negative result is real. The causal reading "because members diverge" is a hypothesis: gaps in the cases where ensembling helped were smaller (MMLU 1.3, PIQA 1.8, HumanEval 3.0, NQ 5.4, TriviaQA 5.4) but MBPP (6.2) tied; one failure case, no controlled test. |
| B5 | Which models form the T2 ensembles | The log says only "top-2 performing models". Choosing by byte accuracy gives Yi+Mistral (MMLU, PIQA, GSM8K), Mistral+Llama2 (NQ, TriviaQA) -- **this is my inference, not in the log** | Q | Write "top-2 models" per benchmark; name the pair only for HumanEval (the log names it). Do not name the other pairs. |
| B6 | Ensembling across vocabularies via universal byte space; simple probability averaging | method statement (idea + log: "simple averaging of probabilities in the universal byte-space") | S | Describe as equal-weight averaging. No weights/tuning in the log. |
| B7 | T2 bold marks | log bolds ensemble in MMLU, PIQA, NQ, TriviaQA and Yi byte in GSM8K (61.5 is the column best); i.e. bold = best in column | S | `figtab-repo`: bold the best number per benchmark column across all rows; GSM8K best is Yi byte 61.5. |

## C. Code models (T3)
| # | Log claim | Recomputed | St. | Report wording |
|---|---|---|---|---|
| C1 | (not stated in log; implied by T3) byte vs token on code | HumanEval@1: CL-7b -3.6 (32.3->28.7), CL-13b -2.3 (35.8->33.5), Yi-Coder -1.9 (38.4->36.5), mean -2.6; MBPP@1: +1.8, -0.2, +0.8 | **must report** | "Byte-level pass@1 is lower than token-level on HumanEval for all three models (by 1.9-3.6 points) and mixed on MBPP (+1.8, -0.2, +0.8)." This contradicts any blanket "no loss" statement. No explanation exists in the log: any is a hypothesis, label as such. |
| C2 | Ensemble of Yi-Coder-1.5B and CodeLlama2-13b improves HumanEval by up to 3.7% over best individual | 42.1 - 38.4 = +3.7 pts over best *token* member (Yi-Coder 38.4); +5.6 over best byte member (36.5) | Q | "+3.7 points over the best individual model (token-level 38.4); +5.6 over the best byte-level member". Not a "%". Ensemble members on HumanEval are byte-level by construction. |
| C3 | MBPP ensemble | 53.6 = best byte member (Yi-Coder 53.6); +0.8 over best token member 52.8; +6.2 over CL-13b | Q | "ties the best byte-level member (53.6)"; no improvement claim. The T3 bold on Yi-Coder 53.6 is a tie with the ensemble. |
| C4 | Ensemble "generally outperformed individual members" | across T2+T3 (7 benchmarks, vs best byte member): 5 improve, 1 tie (MBPP), 1 lose (GSM8K) | Q | Report the 5/1/1 split. |

## D. Beam ablation (T4)
| # | Log claim | Recomputed | St. | Report wording |
|---|---|---|---|---|
| D1 | Beam 1->4 gives consistent improvement up to ~2.9% | PSM 65.7/66.8/67.7 (gain vs beam 1: +1.1 at width 2, +2.0 at width 4); SPM 63.9/65.9/66.8 (+2.0, +2.9) | Q | "up to 2.9 points (SPM) and 2.0 points (PSM), monotone in beam width (1, 2, 4)". Peak 67.7 PSM at beam 4: correct. |
| D2 | Beam-1 row equals Table 1 byte greedy | 65.7/63.9 = T1 byte greedy | S | Internally consistent; implies "greedy" = beam width 1. Table caption in log says "Pass Rate on HumanEval" (no @k stated): write "pass rate" without asserting greedy vs @k beyond the beam-1 identity. |
| D3 | Cost/runtime of beam | not in the log | - | Do not claim any speed/efficiency result. |

## E. Synthetic / qualitative (no table)
| # | Log claim | Evidence | St. | Report wording |
|---|---|---|---|---|
| E1 | 1st-order Markov chain: P("A" | "A") = 0 in token space vs 1-alpha truth | Fig. 2 (token vocabulary {A,B,AA}; red 0.0 arrows from token "A" to "AA"/"A") | S | Mechanism is exact and follows from the vocabulary/BPE; no numeric experiment, alpha not given. |
| E2 | 3rd-order chain: tokenized model "severely biased"; correction "accurately recovers" P(x_{n+1}\|x_{n-2}^n) | Fig. 3 (read): biased estimate ~0 for 6 of 8 three-byte contexts (it matches truth only for BAA, ~0.77; AAA ~0.12 vs truth ~0.30); corrected bars match ground truth visually in all 8 | Q | "visually indistinguishable from ground truth in Fig. 3"; no error metric (KL/MAE) exists in the log: do not quote one or the model size beyond "GPT-2 architecture, 6 hidden layers" (log). Figure plots the probability the next byte is "A". |
| E3 | Same-model prediction of correct completions where standard fails (Fig. 1) | Fig. 1/qualitative | S | Illustrative only. |

## F. Cross-cutting
- **Statistics (Q):** every number is a single value; the log contains no seeds, intervals, test sizes or paired tests. Differences below ~2 points should be described without significance language. My rough unpaired binomial SEs in `byte_minus_token.csv` use benchmark sizes that are *external to the log* (planning estimates): use them only to judge wording, never print them or benchmark sizes in the paper.
- **Naming (Q):** T1/Fig. 6/setup list "CodeLlama-7b"; T3 and the setup list "CodeLlama2-7b" and "CodeLlama2-13b". Use each name as the log gives it; do not claim they are the same or different models and do not add versions. The T2 prefix "Llama2-7B", "Yi-1.5-6B", "Mistral-7B-v0.3" are as logged.
- **Metric labels:** T1 "Pass rates (Greedy and @10)"; T3 "@1"; T2 "Accuracy (Token-level vs Byte-level)". No shot counts, prompts or decoding settings for T2/T3 are given: say "not specified".
- **Hypothesis vs. result:** the log explains results (mid-token OOD tokenization; divergent members) without ablations; present these as interpretations.
