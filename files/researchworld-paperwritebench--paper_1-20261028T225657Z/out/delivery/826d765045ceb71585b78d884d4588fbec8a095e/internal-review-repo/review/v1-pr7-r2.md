# Review round 2: paper-repo PR #7 (Version 1 into `release`)

Inspected commit: paper-repo `15e9f170648dfb556693e834a8b2b4707c2a288b` (PR head = main).
Changes since round 1 (`b44306c`, record `review/v1-pr7.md`): text trimmed (#10), rethinking
figure capped (#9). Rebuilt from `git archive` as in round 1: 0 undefined refs/cites, no errors,
15 pages, references begin on p.12 (main text still runs onto p.12).

## Status of round-1 findings
- M1 binary reward vs shaped reward in code (experience_maker.py L1327–1341): **OPEN** —
  still "binary correctness reward" in Abstract, §1 (l.89), §2 (l.104), §3.3 (l.165 "never
  rewarded for reflecting for its own sake").
- M2 "more often on hard benchmarks": abstract **fixed**; §3.3 (l.165) still "much more often on
  difficult benchmarks than on easier ones" → **OPEN**.
- M3 (a) VL-Reasoner "rarely reflects" (l.87, l.150): **OPEN**; (b) "accuracy gains come without
  lengthening every response" (§4.4): **OPEN**.
- M4 Fig. 5 legibility (figtab-repo#4) and main text > 11 pages: **OPEN** (fig_training_dynamics.tex unchanged).
- m1 "between two and eight times" (l.243) → 2.5–4.6×: **OPEN**.
- m2 Fig. 5(b) caption 0.3–0.9 vs §4.4 0.3–0.8: **OPEN**.
- m3 reading of table_im rows (no-SSR / data rows without FR) stated as interpretation: **OPEN**.
- m4 "best on all seven" at 7B → "among models with reported results": **OPEN**.
- m5 neurips_2025.sty availability decision recorded: **OPEN**.
- m6 benchmark-evaluation decoding (scripts/eval_vlm_new.sh) in §4.1: **OPEN** (only training-time
  validation temperature is given).

Verdict: REQUEST CHANGES.

## Update (figtab-repo#4 answered)
Checked paper-repo PR #11 head `dbbb30b8fe6bc37324fde9464167315c121b31da` (rebuilt, 0 undefined):
Fig. 5 panels stacked at 0.85/1.0 \textwidth; tick labels and legend now legible on p.10. The
figure part of M4 is resolved once #11 is merged into the version's head; the page budget (main
text still reaches p.12–13 in the stand-in layout) remains with paper-repo. m2 (0.3–0.9 caption vs
0.3–0.8 text) is still open.
