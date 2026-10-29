# Review: paper-repo PR #7 (Version 1 into `release`)

Inspected commit: paper-repo `b44306c65483081b62960dc84057356249f16129` (PR #7 head = `main`).
Also read the earlier draft at `5520ac0` (difference: only figure heights of Fig. 3/4).

## What I did
- Fresh `git archive` of the head; pdflatex → bibtex → pdflatex ×2 with local stand-ins for
  `neurips_2025.sty` (Times, 5.5in×9in), `inconsolata`, `stackengine`, `ulem` (absent from this
  sandbox's TeX Live; same as paper-repo's build). 0 undefined citations/references, no LaTeX errors.
  `references.bib` byte-identical to the frozen input (its 34 BibTeX syntax errors are stray commas
  before `abstract` fields in the input; only abstracts are dropped, harmless).
- 16 pages; main text ends on p.12, references begin p.12.
- Opened every rendered page and all seven figure images; Fig. 1 (method overview) is on p.2.
- Traced every number in abstract, intro, §4 and captions to `tables/*.tex` and the figure images:
  all margins, means (46.6/45.2/43.5/42.7), base-model gains, 32B gains and Fig. 6 values check out.
  The ten points of my paper-repo#3 are handled.
- Checked method text against `code/` (experience_maker.py, replay_buffer.py, train_vlm_multi.sh):
  triggers, skip prob 0.35, group_score>0.7 rule, ≤2 kept rethinks, 30–1024 tokens, FIFO buffer
  len/2, |A|+1e-4, 10% all-correct mix, lr 1e-6, T=1.0/top-p 0.95, val T=0.6, aux 0.05, no KL: correct.

## Findings (verdict: REQUEST CHANGES)

### Major
M1. **Reward is described as binary, but the released code shapes it.**
`experience_maker.py` L1327–1341 (training path, `not is_eval`): invalid responses get −0.1;
a correct, non-forced response with 1–2 native reflection markers ("wait,", "wait a",
"alternatively") gets **1.1**; a correct one with ≥3 markers gets max(1−0.2·n, −0.1).
The paper states a binary correctness reward (Abstract; §2 r(x,y)=𝟙[…]; §1 "rewards remain
binary"; §3.3 "the policy is never rewarded for reflecting for its own sake"). This is the
central mechanism behind the "learns to rethink selectively" claim, so the text must describe the
reward the code implements (or state explicitly that the reported models used a different
setting, with evidence). Owner: paper-repo.

M2. **"Rethinks far more often on hard benchmarks than on easier ones" is contradicted by Fig. 6.**
Rethinking ratio ≈78% MathVerse (acc 54.2), 36% MathVision (32.3), 24% MathVista (74.9),
18% MMMU-Pro (41.7): the ratio does not track difficulty (the hardest-by-accuracy MMMU-Pro has
the lowest ratio). §4.4 words this correctly ("adapts ... to the benchmark"); the Abstract
(last sentence) and §3.3 ("much more often on difficult benchmarks") must match it.

M3. **Claims without data.**
(a) VL-Reasoner "rarely reflects" / RL "does not by itself produce reflective behavior" (§1, §3.3):
no rethinking ratio for VL-Reasoner or the base model is in the supplied data (Fig. 6's line is
VL-Rethinker only). (b) "the gains in accuracy come without lengthening every response" (§4.4):
no response-length data exist. Hedge as hypothesis/observation or drop.

M4. **Figure 5 is unreadable at print size and the main text overruns the 11-page target.**
Fig. 5 puts a 3-panel histogram and a line plot side by side at ~0.45\textwidth each; tick
labels/legends are ~3–4 pt. Meanwhile Fig. 3 and Fig. 4 leave large blank margins. Main text
runs to p.12 (target ~11). Owner: figtab-repo (figures/), paper-repo (layout).

### Minor
m1. §4.4 "between two and eight times the improvement of test-time forcing": actual ratios
8.46/2.49=3.4, 3.52/0.76=4.6, 1.98/0.80=2.5, 1.84/0.53=3.5 → "2.5–4.6 times".
m2. Fig. 5(b) caption "|adv| ≈ 0.3–0.9" vs §4.4 "0.3 and 0.8": harmonize.
m3. Table 3 / §4.3 treat the no-SSR and data-mix rows as without Forced Rethinking; `table_im`
does not state this. Say it is our reading of the ablation table (the 28.5 < 29.8 pattern supports
it for the SSR rows; the data rows are ambiguous).
m4. "best on all seven benchmarks" at 7B: several baselines have "-"; add "among models with
reported results".
m5. `neurips_2025.sty` is neither in the frozen inputs nor in the delivered tree; record (in the
PR/README) the venue decision on whether the caller workspace provides it.

## External-review view
The paper answers the objective: method, both components, ablations, dynamics, and both scales
with honest comparisons. A referee would mainly press on M1 (is the "self-reflection" partly
reward-shaped rather than emergent?), M2/M3 (selective-rethinking claims), single-run ablations
(stated for Fig. 5; should also be stated for Table 3), and evaluation protocol details (decoding
for benchmark evaluation is not given — `scripts/eval_*.sh` could supply it).
