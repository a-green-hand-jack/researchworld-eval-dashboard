"""Fill the NeurIPS 2026 checklist template (paper/tpl/checklist.tex) -> paper/checklist_filled.tex"""
import re
A = [
 ("Yes", "The abstract and introduction state the claims (rule-dependent minimum investment, three cost measures, no uniformly hardest rule) and the assumptions; each claim is supported by a numbered result in Sec.~\\ref{sec:results} and the limits are stated in Sec.~6."),
 ("Yes", "Sec.~6 (Discussion and limitations) lists nine limitations, including static rivals, no spillover, noise-free scores, three boards, the exploratory design and the top-100 pool for ordinal rules."),
 ("Yes", "Propositions 1--4 state their assumptions; complete proofs are in App.~\\ref{app:proofs}. The ordinal MILP encoding is argued in App.~\\ref{app:proofs} and checked against brute force."),
 ("Yes", "Sec.~\\ref{sec:setup}, Sec.~\\ref{sec:framework} and App.~\\ref{app:repro} give data versions, targets, caps, margins, solver settings and statistics; the README lists commands and seeds."),
 ("Yes", "All code and a README with environment, download scripts, data versions and SHA-256 checksums, seeds, commands, run times and a table-to-script map are provided (anonymised archive); the data are public."),
 ("Yes", "No models are trained. Boards, target sets, caps, seeds, bootstrap sizes and solver limits are specified in Sec.~\\ref{sec:setup}, the experiment subsections and App.~\\ref{app:repro}."),
 ("Yes", "Medians with IQRs over targets, Wilcoxon signed-rank tests with Holm correction, bootstrap intervals over targets, and bootstrap/subsampling/synthetic replicates are reported; what each interval captures is stated. The core computations are deterministic given the board."),
 ("Yes", "App.~\\ref{app:repro}: CPU only (shared 40-core machine, no GPU), about 20 CPU-hours in total (upper estimate), which exceeded the 4 CPU-hour planning estimate; abandoned or failed runs are listed."),
 ("Yes", "The study uses only public aggregate scores and does not involve human subjects, personal data or model training; we reviewed the Code of Ethics and see no deviation."),
 ("Yes", "Broader impact paragraph in Sec.~6: the analysis could inform benchmark design (positive) and could in principle guide gaming (negative); the case study is descriptive and makes no claim about specific developers."),
 ("NA", "No models or scraped datasets with misuse risk are released."),
 ("Yes", "Assets are cited with versions and URLs (HELM v1.13.0, code Apache-2.0; Open LLM Leaderboard snapshots by commit). Licences for the score data are not declared; this is stated in App.~\\ref{app:repro} and only aggregate scores are used."),
 ("Yes", "The released code is documented in the README (what each script does, inputs, outputs, run times). No new dataset is released apart from small derived result tables."),
 ("NA", "No crowdsourcing or human subjects."),
 ("NA", "No human subjects."),
 ("Yes", "The research (study design, code and drafting) was carried out by an autonomous LLM-based research agent; this is declared in App.~\\ref{app:repro}. LLMs are not a component of the evaluated methods."),
]
s = open('paper/tpl/checklist.tex').read()
s = re.sub(r"%%% BEGIN INSTRUCTIONS %%%.*?%%% END INSTRUCTIONS %%%", "", s, flags=re.S)
i = [0]
def ans(m):
    a = A[i[0]][0]; return "Answer: \\answer%s{}" % a
def jus(m):
    j = A[i[0]][1]; i[0] += 1; return "Justification: " + j
s = re.sub(r"Answer: \\answerTODO\{\}[^\n]*", ans, s)
s = re.sub(r"Justification: \\justificationTODO\{\}", jus, s)
assert i[0] == len(A) == 16, i
open('paper/checklist_filled.tex', 'w').write(s)
print('ok', i[0])
