# Review standard for the VL-Rethinker write-up

Owner: internal-review-repo (review + external review). Source of the standard:
the `Research objective` issue (#1), `/initial-state/inputs/0/INSTRUCTIONS.md`,
`AGENTS.md`/`CLAUDE.md` (identical), the frozen tables, figures, code and
`references.bib`. A version into `release`/`final` of `paper-repo` is approved
only if every item below holds at its head commit, checked by me on the
delivered files (compiled PDF, every figure opened).

## A. Deliverable form (hard requirements)
1. `template.tex` at the delivery root is a complete paper that compiles with
   pdflatex+bibtex (neurips_2025 preprint style, unchanged preamble style,
   `\graphicspath` kept/working, watermark kept), no undefined refs/citations,
   no `filecontents` bibliography; `\bibliography{references}` uses an
   external `references.bib` identical to the supplied one (no edits).
2. ~11 pages of content in the (double-column-target) layout requested; uses the space, not padded.
3. Sections: Abstract (one paragraph, no formulas), Introduction (with
   contributions; method overview figure on p.2), Preliminaries, Method,
   Experiments, Analysis/ablations, Related Work, Conclusion. No
   Acknowledgements, Limitations or Future-Work sections.
4. Every figure/table path in the tex resolves in the delivered tree; all 7
   figures and 3 tables used (or omission justified), each referenced in text.
5. Only keys present in `references.bib`; multiple citations per section,
   Related Work well cited; no invented references.

## B. Scientific accuracy (every number traced to the frozen data)
1. Every number in text/abstract matches tables `table_rr`, `table_le`,
   `table_im` or values printed in the figures.
2. Comparative claims ("SoTA", "+x over best") must be true under the table
   values themselves. Known traps in the supplied material (must be handled,
   not copied):
   - table_le (7B): underlined "prev SoTA" for MathVista (70.2) and MathVerse
     (47.9) ignores MM-Eureka-7B (Qwen) 73.0 / 50.3, so the Δ row's +4.7 and
     +6.3 are vs OpenVLThinker, not vs the best prior 7B reasoning model
     (true margins +1.9 / +3.9).
   - table_rr (72B): MathVision Δ +6.8 is vs Qwen2.5-VL-72B (38.1); the best
     open model listed is Qwen2.5-VL-32B 38.4 (margin +6.5). MMMU Δ -1.4 does
     not match any listed value (QvQ-72B 70.3 -> -1.5; Llama4-Scout 69.4 -> -0.6).
     Bold 68.8 on MMMU is not the best open result; bolding of MEGA/MMMU etc.
     must reflect the scope stated in the caption (open-source vs all).
   - Proprietary o1 is better than VL-Rethinker-72B on MathVision, MMMU-Pro,
     MMMU, EMMA, MEGA: no "beats proprietary" overclaim beyond MathVista/MathVerse.
   - VL-Rethinker-32B row (incl. weak MEGA 19.9) must be reported honestly, not hidden.
   - Overview's "2–6 points over OpenVLThinker/R1-OneVision" vs actual margins.
   - Overview's ablation chain "32.3→29.8→26.0" conflates two rows; table_im
     gives 32.3 (full) / 29.8 (w/o FR) / 28.5 (Filter, no SSR) / 26.0 (plain
     GRPO), and no-SSR rows also lack Forced Rethinking unless stated.
   - Data size: overview says ~38.9K queries; ablation table says 16K for the 7B
     run (13K/11K in data ablations). Text must reconcile (curated pool vs
     subset used), not state one silently.
   - foret_ablation baseline MathVerse 53.13 vs table_im 53.2 (rounding mismatch)
     and the meaning of "(bound)" and "Rethinking Ratio" must be defined, not guessed.
3. Figure captions describe what the figure shows (the supplied summary
   mislabels `rethinking.jpg` as vanishing advantages: it is a forced-rethinking
   example + word cloud; `adv_histogram.jpg` shows advantage distributions).
4. Method is faithful to the code (`experience_maker.py`, `replay_buffer.py`,
   `loss.py`, `train_vlm_multi.sh`): GRPO advantage, SSR buffer of
   |A|>0 samples with replay prob ∝ |A|^α, forced-rethinking triggers
   ("Wait, does it seem right?", "Wait, let's double check", "Wait, there might
   be a mistake"), fraction q, keeping only correct rethinks, SFT term;
   hyperparameters stated only if found in code/scripts.
5. Claims about training dynamics read off `ssr_eval_curve.jpg` and
   `vanishing_adv.jpg` correctly (e.g. effective-query ratio falls ~0.41→0.20
   over 15×16 steps; GRPO val reward peaks ~0.43 then declines, SSR ~0.455).
6. No claim of statistical significance, seeds or error bars that the data
   lack; single-run nature stated where it matters (ablations).

## C. External-review questions the paper must answer
- Is gain from SSR vs Filter vs data mix separable? (table_im)
- Why selective rethinking, and what does the "bound" mean? (foret_ablation)
- Evaluation protocol (greedy? temperature? answer extraction) and which
  baseline numbers are reproduced (†) vs quoted.
- Relation to prior RL-for-VLM work (R1-V, MM-Eureka, OpenVLThinker,
  R1-OneVision, DAPO-style dynamic sampling, prioritized experience replay).
