# NOTES (agent working memory; not a deliverable)
- Env: 4-CPU cgroup quota (nproc lies: 40), no GPU, no API key. Proxy allows HF + PyPI. venv at /work/venv (torch cpu, transformers 5.22, llama-cpp useless: 2 tok/s).
- Venue: ICML 2026 (template in /work/paper, from media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip). 8 pages main body, refs+appendix unlimited. Impact statement required. No checklist mandated by ICML (add reproducibility checklist appendix anyway).
- Data: MMLU-Pro rev b189ec76 in /work/data/mmlu-pro (never run scripts from there). Pool = 1500 random questions with <=200 Qwen tokens (seed 12345), see code/common.py.
- Main run started 2026-11-11 20:14 UTC: `score_matrix.py models/Qwen2.5-1.5B-Instruct results/q15 1500 150 4` (40 configs = 8 instr x 5 demo sets; chunk-major; ~1.25 s/(cfg,q) => ~25h). log: logs/q15.log. Resumable (skips existing npz).
- Design: cached outcome matrix Y[K,N]; simulate search episodes (dev set iid from pool; truth = pool accuracy of selected config); optimizers: grid, random, SH, minibatch(MIPRO-like), greedy; reporting: naive, holdout split, CV, optimism bootstrap, max-t, conditional (polyhedral), ladder. Conclusion experiments: lift vs baseline, budget-confounded comparison. Synthetic IRT sim for controlled factors + theory.
- DO NOT search for/read the forbidden paper (prompt-optimization reporting-gap paper). Only use classic stats literature.

## Update 2026-11-12 ~03:00
- World A (q15, Qwen2.5-1.5B, A-grid K=40): flat (config sd ~0.8pt, rho .78). Running to chunk 4 (N=750), then chain.sh (/tmp/chain.sh) kills it and starts b15 (1.5B with B-grid, results/b15) ~8h.
- World b05 (Qwen2.5-0.5B, B-grid K=40, N=750) DONE: results/world_b05.npy; sd 2.2pt, split-half reliab .66. sim outputs in results/sim/{gap,ksweep,conclusions,norepl}_b05.parquet (gap run used OLD episodes.py before maxt/EB extended to adaptive optimizers -> rerun final).
- Key b05 numbers: naive gap n=50:7.8pts n=100:5.1 n=200:3.1 (grid). EB best RMSE, holdout unbiased; maxt conservative; cond poor; boot residual bias.
- synthetic: gap = sigma_n*sqrt(1-rho)*m_K verified (results/sim/synth_sweep.parquet; fig synth_collapse).
- Paper: /work/paper/main.tex + sections/{related,setting,protocols}.tex written; TODO abstract,intro,experiments,discussion,impact,appendix; numbers.tex macros; figs via code/make_figs.py.
- Worlds to run final: q15, b05, b15, mix(q15+b05), maybe mix3. Then exp_main gap/ksweep/conclusions/norepl each (R=1000-2000).

## Update 2026-11-12 ~14:00 (state)
- Paper compiles (paper/main.pdf, ICML 2026 template, main body ends p.7, 14pp total with refs+appendix). Sections in paper/sections/*.tex; tables auto-generated into paper/tables/*.tex by code/make_tables.py (full tabular envs); figs by code/make_figs.py (all). numbers.tex is empty (numbers typed in prose; each verified against tables).
- Worlds used in paper: q15 (A), b05 (B), mix = q15 U b05 (K=80). Sims done for all three (gap R=2000, ksweep, conclusions, norepl, optsens) in results/sim.
- b15 (1.5B on B-grid, "world C") is still generating (results/b15, log logs/b15.log; ~110 units left at 13:30) -> when done: python code/build_worlds.py 750; run exp_main.py b15 {gap,ksweep,conclusions,norepl,optsens} 2000; add 'b15' to WORLDS lists in make_tables.py/make_figs.py (WCOL/WN already have b15) and update text (appendix says world C not used).
- TODO before finishing: verify every number in prose vs tables; update README artifact map; delete results/sim_test; final compile & check page limit (<=8 main).

## FINAL (2026-11-13 ~04:30): all experiments done (worlds q15,b05,mix,b15,s17), paper compiled (17pp; body ends p.7), README complete, reproducibility spot-check passed.
