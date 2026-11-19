"""Fill the NeurIPS checklist template (tmpl/checklist.tex) -> checklist_filled.tex (answers below)."""
import re
src = open("paper/tmpl/checklist.tex").read()
# drop the instruction block
src = re.sub(r"%%% BEGIN INSTRUCTIONS %%%.*?%%% END INSTRUCTIONS %%%", "", src, flags=re.S)
# remove the paragraphs that precede it (they are instructions as well) but keep the heading
head = "\\section*{NeurIPS Paper Checklist}\n"
src = head + src[src.index("\\begin{enumerate}"):]
A = [
 ("Yes", "Abstract and Sec.~\\ref{sec:intro} state the three claims; every number is from Sec.~\\ref{sec:exp} and the scope (two small models, one benchmark, fixed-candidate search) is stated in the abstract and Sec.~\\ref{sec:limits}."),
 ("Yes", "Sec.~\\ref{sec:limits} ``Limitations'' covers models, tasks, search space/optimisers, simulation design, protocols and deviations."),
 ("Yes", "Propositions 1--3 state assumptions and include proofs in Sec.~\\ref{sec:theory}; Prop.~2 is explicitly a Gaussian approximation and is tested empirically; max-$T$ coverage is asymptotic and is stated as such."),
 ("Yes", "Sec.~\\ref{sec:setup} and App.~\\ref{app:repro} give data revision, models, search space, scoring rule, pool construction, simulation protocol, replicate counts and seeds; code reproduces all tables and figures."),
 ("Yes", "All code, the cached correctness matrices' generation scripts, exact commands, versions and expected runtimes are in the supplementary code package (README.md). Data and models are public (MMLU-Pro revision b189ec7, Qwen2.5)."),
 ("Yes", "Sec.~\\ref{sec:setup}: pool/benchmark construction, search space and optimisers; no model is trained; no protocol hyperparameter was tuned on reported results (App.~\\ref{app:repro})."),
 ("Yes", "Replicate-level 95\\% CIs ($\\pm1.96$ s.e., $R=1000$ or 300) are given for gaps; coverage is reported as a proportion over replicates (accurate to about $\\pm1.5$ pts, Sec.~\\ref{sec:limits}); the single real selection on fresh questions has a Wilson CI. Variability captured: random benchmark draw, candidate subset and algorithmic randomness, with the LLM outputs fixed."),
 ("Yes", "App.~\\ref{app:repro}: CPU-only Xeon Gold 6230 (shared), 4 threads per job, wall-hours per matrix and total; preliminary runs disclosed."),
 ("Yes", "The work uses public data and models, involves no human subjects, and follows the Code of Ethics."),
 ("NA", "Methodological study of evaluation practice with no direct deployment path; indirect positive impact (more reliable reporting) is mentioned in the Introduction; we see no specific negative societal impact."),
 ("NA", "No models or data with misuse risk are released."),
 ("Yes", "MMLU-Pro (MIT, revision b189ec7) and Qwen2.5-0.5B/1.5B-Instruct (Apache-2.0) are cited with versions and licences (Sec.~\\ref{sec:setup}, App.~\\ref{app:repro}); licences verified from the hub metadata."),
 ("Yes", "The released code package documents all scripts; no new datasets or models are released."),
 ("NA", "No crowdsourcing or human subjects."),
 ("NA", "No human subjects."),
 ("Yes", "LLMs (Qwen2.5-0.5B/1.5B-Instruct) are the object of study and are fully described in Sec.~\\ref{sec:setup}; an AI assistant was also used for code and drafting, which does not affect the scientific method beyond the scripts released."),
]
parts = src.split("\\item[] Answer: \\answerTODO{} % Replace by \\answerYes{}, \\answerNo{}, or \\answerNA{}.\n    \\item[] Justification: \\justificationTODO{}")
assert len(parts) == len(A) + 1, (len(parts), len(A))
out = parts[0]
for (a, j), rest in zip(A, parts[1:]):
    out += f"\\item[] Answer: \\answer{a}{{}}\n    \\item[] Justification: {j}" + rest
open("paper/checklist_filled.tex", "w").write(out)
print("ok", len(A))
