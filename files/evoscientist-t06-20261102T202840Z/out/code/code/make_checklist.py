"""Fill the NeurIPS checklist template (paper/checklist_template.tex) -> paper/checklist.tex."""
import os, re
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
t = open(os.path.join(ROOT, "paper", "checklist_template.tex")).read()
t = re.sub(r"%%% BEGIN INSTRUCTIONS %%%.*?%%% END INSTRUCTIONS %%%", "", t, flags=re.S)
A = [
 ("Yes", "Abstract and Sec.~1 state the scope (adjacent-pair BT sensitivity on four public boards), the exploratory status of the $\\kappa$ regularity, and the limits."),
 ("Yes", "Sec.~6 (Discussion and limitations) lists eight limitations: greedy upper bounds, realisability, few boards, model assumptions, bootstrap $z$, statistics, scope, omitted phenomena."),
 ("Yes", "One heuristic first-order proposition (Sec.~3) with assumptions and a short Cauchy--Schwarz proof; it is explicitly labelled heuristic."),
 ("Yes", "Sec.~3--4, App.~A and the released README give the model, adversary, data versions and checksums, seeds and commands."),
 ("Yes", "Code is in the supplementary material; all data are public with versions and sha256 in App.~A (data files are not redistributed). README lists the script for every table and figure."),
 ("Yes", "No training is involved; model hyperparameters ($\\lambda$, bootstrap sizes, chunking rule, thresholds) and their sensitivity are given in Sec.~3--5 and App.~B."),
 ("Yes", "Percentile bootstrap intervals over pairs/seasons, bootstrap over votes for $z$, 30 repetitions for random edits; sources of variability and caveats (dependence, few pairs) are stated."),
 ("Yes", "CPU only; the whole pipeline takes a few minutes on 20 cores (README gives per-script estimates)."),
 ("Yes", "Only public, anonymised comparison data were used; no human subjects were contacted."),
 ("Yes", "Sec.~6 (Broader impact) discusses use for defence and the risk of illustrating how few edits reorder close contestants."),
 ("NA", "No models or new datasets are released; only analysis code."),
 ("Yes", "Arena 55k (apache-2.0), MT-Bench judgments (cc-by-4.0) and FiveThirtyEight NBA Elo (CC-BY-4.0) are cited with versions in App.~A."),
 ("Yes", "The released analysis code is documented in the README."),
 ("NA", "No crowdsourcing was performed; existing public vote data are re-analysed."),
 ("NA", "No new human-subject research was performed."),
 ("Yes", "App.~A discloses that an LLM assistant planned the study, wrote the code and drafted the paper; all numbers come from the released scripts."),
]
assert t.count("\\answerTODO{}") == len(A), t.count("\\answerTODO{}")
for ans, just in A:
    t = t.replace("\\answerTODO{}", "\\answer%s{}" % ans, 1)
    t = t.replace("\\justificationTODO{}", just, 1)
open(os.path.join(ROOT, "paper", "checklist.tex"), "w").write(t)
print("checklist written")
