# Study plan: ICLR 2025 paper on exact byte-level probabilities from tokenized LMs

The task has no new experiments to run: the "study" is a faithful, scientifically sound write-up of the supplied
idea, experimental log (inside `/initial-state/inputs/0/INSTRUCTIONS.md`, sections `[RESEARCH IDEA]`,
`[EXPERIMENTAL LOGS]`, `[AVAILABLE FIGURES]`) and six figures, with a real, pre-2024-10 bibliography.
Deliverables (world-required): `template.tex`, `template.pdf` (pdflatex+bibtex, <=10 main pages), `references.bib`;
plus what they need to compile: ICLR style files, `figures/`, `tables/`.

## Division of the work (see CODEOWNERS PR in paper-repo)
| Function | Position | Delivers / does |
|---|---|---|
| context | idea-repo | Brief: method (valid/cover encodings, byte-token lemma, reverse search, ensembling), claims, related-work map, **verified real citations <= 2024-10** with BibTeX (token healing, token alignment, FIM, BPE, benchmarks, models, ensembling, byte-level LMs) |
| analysis | experiment-repo | Claim ledger: every number/claim in the log, recomputed from the four tables; flags inconsistencies; says what each claim can and cannot support; no new numbers |
| presentation | figtab-repo | `figures/` (the 6 supplied PNGs, checked legible), `tables/*.tex` for Tables 1-4 in ICLR style (caption above, bold best, N/A handled) |
| venue + report | paper-repo | `template.tex`, `references.bib`, `template.pdf`, style files; 10-page budget, anonymity, compile-clean |
| review | internal-review-repo | judges against the objective; checks every number against the log |

## Storyline (one claim per section)
1. Problem: tokenization bias (prompt ending mid-token gives zero probability to correct continuation; vocabularies
   incompatible for ensembling). Fig 1, Fig 2.
2. Method: exact next-byte distribution from token logits by marginalizing over valid encodings; cover encodings;
   reverse search (Alg. 1, Fig 4); sampling (Fig 5); zero-shot wrapper. Formal: definitions + the Byte-Token
   Representation Lemma derived logically from the idea, no claims beyond the supplied material.
3. Evidence (in this order): synthetic recovery (Fig 3: 3rd-order Markov chain; Fig 2: 1st-order, P(A|A)=0 vs 1-alpha);
   FIM (Table 1 / Fig 6); ensembling (Tables 2, 3); beam ablation (Table 4).
4. Honest limits: byte-level single models are not uniformly better (HumanEval @1 drops for all three code models,
   Llama2 GSM8K 15.1 -> 12.5); ensemble hurts when members diverge (GSM8K 55.8 < 61.5); MBPP ensemble ties best member (53.6);
   baselines N/A in PSM; compute cost not measured in the log (do not claim speed).

## Known traps in the log (to resolve before drafting; owner: experiment-repo, then paper-repo wording)
- "18% improvement ... in SPM": 63.9 vs 45.0 is +18.9 points (+42% relative). State as points, not an unqualified "%".
- Beam "up to ~2.9%": SPM 63.9 -> 66.8 (+2.9 pts); PSM 65.7 -> 67.7 (+2.0 pts). Say points; state that Table 4 metric is
  pass rate (greedy decoding assumed only if the log says so: it does not, so do not assert it).
- "CodeLlama2-7b/13b" in Table 3 vs "CodeLlama-7b" in Table 1/Fig 6: use the log's names as given; do not add details.
- Ensemble member identities are given only for HumanEval (Yi-Coder-1.5B + CodeLlama2-13b, +3.7 over 38.4 = 42.1); for the
  other columns say "top-2 models" as the log does.
- Knowledge isolation: no hyperparameters, datasets sizes, shot counts, hardware or author-level facts beyond the log.
  Absent details are stated as not specified, or omitted, never invented.
- Cited related work must be real and dated <= 2024-10; the method paper itself must not be recalled or cited.
