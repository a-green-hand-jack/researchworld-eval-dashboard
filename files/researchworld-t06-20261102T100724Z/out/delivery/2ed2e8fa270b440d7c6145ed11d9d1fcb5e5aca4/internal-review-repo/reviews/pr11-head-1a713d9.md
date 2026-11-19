# Review of paper-repo#11 (into `final`), head 1a713d96b412f63c34b1a9d013a7ec3a3c197b1e

## Inspected
- paper/main.pdf (17 pp; main text pp.1-9, references from p.9; `venue/tools/check_pdf.py` PASS), clean rebuild from main.tex gives identical text, no undefined refs.
- `paper/make_numbers.py` rerun: `numbers.tex` identical. `figures/make_figures.py` rerun: T1-T3 identical, F1-F7 regenerate.
- All 7 figures opened (rendered, labelled, legible). `code/test_btlib.py` passes.
- Independent check (own code, raw MT-Bench human parquet, pinned sha256 4877bc46...): BT fit gives GPT-4 top, z = 4.105 (paper 4.11); exact-refit greedy removal flips top-1 after 92 removals (paper k* = 92, Table 1).
- Numbers in text spot-checked against results/*.csv (Fig 2 rank-2 numbers: random_curve.csv claim_id 2, 14/200 at k=500; approx_check max error 45% at k*).

## Verdict
Substantively sound, honest and reproducible in its core; request changes on a short list of concrete defects (below). None needs new experiments.

## Findings
1. Text error: "BT agrees with FiveThirtyEight's Elo ... across 72 seasons" (§4.5). results/sanity_fit.csv has 69 NBA seasons (+3 non-NBA rows with NaN); `make_numbers.py` line 194 uses len(sn). The means (0.83, 68%) are correct; n should be 69.
2. Figure 2 does not show the claims behind the headline random-vs-worst-case numbers. F2 plots C1 and C2 r=1 only. The abstract/§4.3/§5 figures (MT-Bench-human rank-2 pair: 500 random removals = 38.5x k*, 7% of draws; Arena rank-2 pair: 2000 = 8.9x, 0%) come from random_curve.csv claim_id 2, which is not plotted, though the text cites Figure 2. The "C2 top adjacent pair" panel for Arena is the near-tie. Add these claims to F2 (or an appendix figure) so the claim is checkable; also disambiguate "rank-2 adjacent pair" from the claim label "C2".
3. Framing of the scaling fit. k* is mechanically tied to the z-gap (distance to flip), so R2 = 0.97 and "largely accounted for by z" is close to a consistency check, not an explanation of design differences. Say so in the abstract and §4.4 and do not present it as the main finding. The abstract's sentence on dataset offsets (two nested parentheticals, run-on) is hard to read; rewrite the abstract so each claim is one checkable statement.
4. "on five size scales" (abstract/contributions) vs four defined (s1-s4) plus absolute k*; make consistent.
5. code/README.md "Known gaps" gives the Wald/bootstrap s.e. ratio as 0.94-1.0 (NBA), 1.05-1.4, "~30%"; results/se_check.csv and the paper give 0.87-1.41 and "up to about 40%". Align.
6. Reproduction: README lists URLs and checksums but no fetch script/commands that verify them; add one (curl + sha256sum for the four files, or a `fetch_data.sh`), as `deliverable.md` asks for data acquisition steps.
7. Hygiene: `figures/__pycache__/*.pyc` are committed; remove and ignore.

## Round 2 (head 2e4c1cb) and round 3 (head 84d209add180c1c107aa8fa6cf88b7f277d336d0)
- Findings 1,2,3,4,7 resolved (checked: numbers.tex identical on rerun, F2 now has the rank-2/3 row, pycache removed, abstract rewritten, clean build, check_pdf PASS, 0 undefined refs).
- 84d209a adds the crowd-vs-3-LLM-judges contrast on identical Arena battles (results/kstar_judges.csv, code/run_judges.py). Reported honestly: pair identity across boards unchecked, cause not identified, licence undeclared (research use, raw files not redistributed). Accepted as stated; no figure yet (paper-repo main has figtab PR #17 for it).
- Findings 5 and 6 are NOT in the head: code/fetch_data.sh is absent and the README s.e. text is unchanged at 84d209a, although paper-repo main (539eb65, 5e377c9) already has them. Head must include current main.

## Round 4: APPROVED at head 0016a0bd97970211267d0497d88ec7af8b2bfee1
Checked at that head: contains current paper-repo main (incl. #15, #17); clean latexmk build, 0 undefined refs, 19 pp, main text ends p.9, check_pdf PASS; rebuilt PDF text equals the committed PDF; make_numbers.py leaves numbers.tex identical; make_figures.py regenerates all figures (F1-F8, T1-T3); F8 (crowd vs 3 LLM judges) opened: labelled, legible, matches text; code/fetch_data.sh present, pins match README, the MT-Bench GPT-4 sha256 verified by download (57068327...); README s.e. text aligned with se_check.csv; figure numbering and file map consistent. Findings 1-7 all resolved; the judge-contrast caveats (pair identity unchecked, cause unidentified, undeclared licence) are stated in the paper. Independent reproduction of MT-Bench-human z = 4.105 and k* = 92 (round 1) stands. Not independently re-run: the Arena-judge numbers (need ~1 GB downloads, ~25 min); they follow the committed script and are caveated.
