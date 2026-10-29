# Study plan and division of work

Objective: `story-repo`#1 (frozen copy `/initial-state/inputs/0/INSTRUCTIONS.md`).
Deliverables (world-required paths, delivered at the root of `paper-repo`): `template.tex`, `references.bib`, `template.pdf`.
The task asks for exactly two outputs (a complete `references.bib` and a complete, self-contained `template.tex`), so every table, algorithm and caption lives inside `template.tex`; no `\input` of extra delivered files except the supplied `math_commands.tex`.

This plan says what the paper must answer, which evidence answers it, and which position delivers each part. It does not prescribe wording or conclusions beyond what the logs show.

## 1. Sources and hard constraints (apply to every position)

| Source | Location | Use |
|---|---|---|
| Research idea | objective issue, `[RESEARCH IDEA]` block | only source for the method |
| Experimental logs | objective issue, `[EXPERIMENTAL LOGS]` block (Tables 1-4 + qualitative notes) | only source for numbers and observations |
| Figures | `/initial-state/inputs/2/figure_{1..6}.png`, captions in `info.json` | only figures allowed; include as `figures/figure_N.png` |
| Style | `iclr2025_conference.{sty,bst}`, `math_commands.tex`, `natbib.sty`, `fancyhdr.sty`, guidelines | unmodified |
| Template | `/initial-state/inputs/9/template.tex` | keep preamble, author block and section skeleton |

- Knowledge isolation: method and results come from the supplied material only. Do not reconstruct the published paper this material derives from, and do not cite it or any preprint of it; prior work by possibly the same authors, if cited at all, is cited in the third person like any other work (decision: `idea-repo`).
- Citations: real papers only, published (first public version) on or before 2024-10, each verified against a bibliographic source (Crossref / arXiv / DBLP / OpenReview / ACL Anthology); only keys present in `references.bib`.
- Anonymity: author block exactly as in the template; no acknowledgements, no self-identifying links.
- Main text <= 10 pages (figures and tables included; references and appendix excluded). Abstract one paragraph.
- Compiles cleanly with `latexmk -pdf` (pdflatex + BibTeX) from a tree holding the supplied style files and `figures/`; no undefined references or citations, no duplicate labels, no overfull boxes that leave the text rectangle.
- Supplied captions refer to "Section 4.1", "Section 4.2", "Figure 4", "Definition 3", "Algorithm 1" of a different numbering. In our paper the method is Section 3; every caption must be rewritten with `\ref` to our own labels (the "Figure N:" prefix in `info.json` is not part of the caption).
- No efficiency/runtime numbers exist in the logs: any cost statement is analytic (complexity, number of model calls), never measured.
- No seeds, variances or sample sizes are logged: no error bars, no significance claims; this is stated as a limitation.

## 2. Claims and the evidence each needs

Numbers below are copied from the logs; `experiment-repo` owns their verification and the derived quantities.

| ID | Claim | Evidence (log) | Figure/table | Section |
|---|---|---|---|---|
| C1 | Conditioning on one deterministic tokenization of the past biases next-byte prediction ("tokenization bias"); on a 1st-order Markov chain the token model gives P("A" after "A") = 0 where the truth is 1 - alpha | qualitative note, synthetic | Fig. 2 (`figure_2.png`) | 3.1 (motivation, analytic example) |
| C2 | For a tokenized LM there is an exact byte-level process obtainable without retraining: P(x_1^n) = sum over cover encodings of P(t); invalid encodings (impossible under the deterministic tokenizer) have zero probability and can be pruned | idea (Byte-Token Representation Lemma); stated and proved in the paper, not measured | Fig. 4 left | 3.2 + proof in appendix |
| C3 | Cover encodings can be found by a backward search that only looks a bounded number of bytes back (longest token length), and the next byte is sampled by summing next-token probabilities over tokens starting with that byte | idea steps 2-4 | Fig. 4 right (Algorithm 1), Fig. 5 | 3.3, algorithm boxes |
| C4 | The correction recovers the true transition probabilities of a 3rd-order Markov chain that the tokenized model gets wrong | qualitative note, synthetic | Fig. 3 | 4.1 |
| C5 | Prompts ending mid-token (SPM infilling) hurt token-level decoding; byte-level decoding removes most of the drop and beats token healing and token alignment | Table 1 (CodeLlama-7b, HumanEval Random Span): SPM greedy 45.0 -> 63.9 (healing 62.7, alignment 63.0); SPM @10 66.5 -> 84.3 (83.8, 82.9); PSM greedy 64.9 -> 65.7, PSM @10 84.0 -> 84.1 | Fig. 6 and/or table | 4.2 |
| C6 | Converting a model to byte level leaves standard benchmark accuracy mostly unchanged, with some drops | Tables 2-3 token vs byte columns (e.g. drops: Llama2-7B GSM8K 15.1 -> 12.5, NQ 25.0 -> 23.4; HumanEval 32.3 -> 28.7, 35.8 -> 33.5, 38.4 -> 36.5) | Tables 2-3 | 4.3 |
| C7 | Byte space lets models with different vocabularies be ensembled by averaging; top-2 ensembles beat the best member on MMLU, PIQA, NQ, TriviaQA and HumanEval, tie on MBPP, and lose on GSM8K where the members differ widely | Table 2 (ensemble 65.4 / 80.7 / 30.0 / 64.2 / 55.8), Table 3 (42.1 / 53.6), voting 62.1 / 80.1 | Tables 2-3 | 4.3 |
| C8 | Beam search over the byte-level procedure helps FIM: width 1 -> 4 gives PSM 65.7 -> 67.7, SPM 63.9 -> 66.8 | Table 4 | Table 4 | 4.4 |

Wording traps the analysis must settle before the text uses them (owner `experiment-repo`):
- "18% improvement" in SPM is 45.0 -> 63.9 = +18.9 percentage points (about +42% relative): report as points.
- "up to 3.7%" ensemble gain on HumanEval is 42.1 vs 38.4 (best member, token-level Yi-Coder-1.5B): points, and say which baseline column.
- "up to ~2.9%" beam gain is SPM 63.9 -> 66.8 (points); PSM is +2.0.
- GSM8K "by 20%": Yi-1.5-6B 61.3/61.5 vs Mistral 39.0 is ~22 points; state the actual numbers.
- PIQA ensemble 80.7 vs best member 80.3 (byte) / 80.1 (token): a small gain; do not overstate.
- Which pair forms the "top-2" per benchmark is only stated for HumanEval (Yi-Coder-1.5B + CodeLlama2-13b); elsewhere say "the two best-performing models" without naming a pair the logs do not name.
- Model names: Table 1 says CodeLlama-7b, Table 3 says CodeLlama2-7b / CodeLlama2-13b; keep the logs' names and do not assert they are different models.
- Bold marks in the logs are not consistent (e.g. Yi-1.5-6B GSM8K byte 61.5 bold, MBPP tie 53.6): bolding in our tables follows one rule stated in the caption.
- Beam search: the logs give widths only; the method text may describe beam search over cover encodings / byte sequences only as far as the idea supports, and flag what is a design description.
- Qualitative FIM failure cases ("delimeter", "collatz", "palindrome"): may be mentioned as named examples; no invented prompt text or outputs.

Negative or mixed results that must appear in the text (not only in tables): byte-level drops on HumanEval for all three code models and on Llama2-7B NQ/GSM8K; ensemble below best member on GSM8K; no ensemble gain on MBPP; tiny PSM gains. Explanations offered for them are labelled as hypotheses.

## 3. Paper outline and page budget (main text <= 10 pp)

1. Introduction (~1.2 pp): tokenization bias, mid-token prompts in FIM, incompatible vocabularies for ensembling; Fig. 1; contribution list matching C1-C8.
2. Related work (~0.8 pp): subword tokenization (BPE, WordPiece, unigram/SentencePiece) and stochastic variants; byte-level / token-free models; marginalising over tokenizations; prompt-boundary fixes (token healing, token alignment); fill-in-the-middle training and evaluation (incl. the Random Span benchmark source); LLM ensembling and vocabulary mismatch; the evaluated models and benchmarks are cited where used.
3. Method (~3 pp): 3.1 notation and tokenization bias (Fig. 2, analytic 1st-order example); 3.2 valid/invalid encodings, cover encodings, Byte-Token Representation Lemma (Fig. 4 left); 3.3 backward cover-encoding search (Algorithm 1, Fig. 4 right) and next-byte probability/sampling (Algorithm 2, Fig. 5), analytic cost; 3.4 uses: FIM decoding, byte-space ensembling by averaging, beam variant.
4. Experiments (~3.5 pp): setup (models, datasets, metrics, baselines, prompt modes); 4.1 synthetic Markov chains (Fig. 3); 4.2 FIM (Fig. 6 + exact numbers); 4.3 token vs byte and ensembling (Tables 2-3); 4.4 beam ablation (Table 4).
5. Conclusion with limitations (~0.5 pp): no runtime measurements, no variance, mixed byte-vs-token results, ensemble divergence limit, tokenizer assumptions (deterministic tokenizers).
Appendix: proofs, full algorithm details, any table moved for space, implementation details as given in the logs.

## 4. Division of work

| Position | Function | Delivers / supplies | To | Standard |
|---|---|---|---|---|
| `idea-repo` | context | Brief (wiki); verified related-work map with real BibTeX entries (<= 2024-10, source checked) and one line each on its relation to this work, incl. Bavarian et al. 2022, token healing (Dagan et al. 2024), token alignment (Athiwaratkun et al. 2024) named in the supplied captions, and the evaluated models/benchmarks; conventions to follow | `paper-repo` (bib + related work), all | every entry resolvable; no key that is not cited, no cited key that is missing |
| `experiment-repo` | analysis | claims-evidence ledger: each number the paper uses traced to its log table, derived differences (points vs relative), settlement of the wording traps in Section 2; check of the method's formal content (definitions, lemma, proof, algorithms) for correctness, e.g. by a small script on a toy tokenizer/Markov chain kept as working material | `paper-repo`, `figtab-repo` | no number in the paper without a log source; negatives stated |
| `figtab-repo` | presentation | LaTeX for Tables 1-4 (or Table 1 replaced by Fig. 6 if no information is lost), figure placement and sizes for Figs. 1-6, rewritten captions with our cross-references, one bolding rule | `paper-repo` | ICLR caption rules (table captions above, figure below, lower case), legible at print size, fits page budget |
| `paper-repo` | venue, report | `template.tex`, `references.bib`, `template.pdf`, plus the supplied style files and `figures/` needed to compile in its repository | delivery | Sections 1-3 of this plan; compiles cleanly; <= 10 pp |
| `internal-review-repo` | review, external-review | approval of versions; reviewer reading | `paper-repo` | objective's requirements |
| `story-repo` | plan | this plan, `.forgejo/CODEOWNERS` in `paper-repo`, check of each version against Sections 1-3 | all | every requirement of the objective has an owner |

Recorded commitments matching this split: `idea-repo`#2, `experiment-repo`#2 (derived numbers in `analysis/derived.json`, Figure 2 check in `analysis/markov_check.py`), `figtab-repo`#2 (Table 1 shown through Fig. 6, which prints the same numbers, with a fallback table), `paper-repo`#2. Where this plan and the analysis disagree on a number or its wording, `experiment-repo`'s `analysis/` decides. Note from it: Table 1 "@10" is the maximum over a temperature sweep (footnote of `figure_6.png`), to be stated in the setup.

Still open for `experiment-repo` once a draft exists: check the method's formal content in `template.tex` (definitions of valid/invalid and cover encodings, the representation lemma and its proof, Algorithms 1-2) for correctness, not only the numbers.

Delivered paths (`.forgejo/CODEOWNERS` of `paper-repo`): `template.tex`, `references.bib`, `template.pdf` are all `paper-repo`'s; the other positions supply material to it, not paths. Build inputs (style files, `figures/` copied byte-identical from the frozen inputs) are unlisted and therefore `paper-repo`'s (pull request `paper-repo`#3).

## 5. Requirement checklist (objective -> owner)

- Title, abstract (one paragraph), introduction, related work, methodology, experiments, conclusion, optional appendix: `paper-repo`.
- Related work with real pre-2024-10 citations, BibTeX: `idea-repo` supplies, `paper-repo` delivers.
- Results match logs, negatives reported honestly: `experiment-repo` verifies, `paper-repo` writes, `internal-review-repo` checks.
- All six figures integrated and referenced, only supplied figures: `figtab-repo` supplies, `paper-repo` delivers.
- ICLR format, anonymity, page limit, compile quality: `paper-repo`.
- Each version checked against this plan: `story-repo`; approved: `internal-review-repo`.

## 6. Version checks against this plan

| Draft (`paper-repo` main) | Result | Open with |
|---|---|---|
| e64a61b10778 (draft v1) | builds cleanly; main text ends on p. 10; C1–C8 covered; log percentages given as points; negative results stated. Open: the title is too close to the source work (knowledge isolation); Fig. 1 continuation wording; procedural details the logs lack (GPT-2 training data, beam definition, reason for voting) | `paper-repo`#6; formal method check `experiment-repo`#3 |
| c76bc2b844ad (draft v3, carried by version PR `paper-repo`#8) | all `paper-repo`#6 points resolved: own title; Fig. 1 continuation is the character `a`; GPT-2 data, beam search and voting worded from the log only, details framed as method description in Appendix A (no measurements); KV-cache sharing stated correctly. Rebuilt from scratch: no warnings, conclusion on p. 10, references from p. 11. Captions of Figs. 2, 3 and 6 checked against the PNGs. Plan sign-off: yes, pending only the formal-method check | `experiment-repo`#3 |
| formal check (`experiment-repo`#3, closed; `experiment-repo` 7fc780361e5a `analysis/method_check.py`, README §6) | Definition 1, Lemma 1, Proposition 1, Eq. (sampling) and Algorithm 1 are correct, checked by proof and numerically on MPE/BPE; the Figure 2 example is reproduced to 1e-16. Three wording fixes, none of which changes a claim: positive-probability qualifier, prefix-closedness of valid encodings, the shared-prefix claim (already corrected in v3 Appendix A). Plan sign-off of the method: yes; the fixes are with the report | `paper-repo`#11 |
