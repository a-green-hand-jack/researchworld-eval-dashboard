"""Fills the official NeurIPS 2026 checklist template (paper/tpl/checklist.tex) -> paper/checklist_filled.tex"""
import re, os
HERE = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(HERE, "tpl", "checklist.tex")).read()
t = re.sub(r"%%% BEGIN INSTRUCTIONS %%%.*?%%% END INSTRUCTIONS %%%", "", t, flags=re.S)
A = [
 ("Yes", "Abstract and introduction state the headroom analysis, the estimators, and the conditional empirical findings (Sections 3--5); the scope is the population mean only, stated in Sections 3 and 6."),
 ("Yes", "Section 6 lists limitations (target limited to the mean, resampling protocol, plug-in headroom estimate, Wald intervals and small-$n$ undercoverage, efficiency statement argued rather than proved, no multiplicity correction)."),
 ("Yes", "Proposition 1 and Corollaries 1--2 are proved in Appendix A with assumptions stated in Section 3 (i.i.d.\\ sampling, finite second moments); the efficiency-bound statement is explicitly marked as argued, not proved."),
 ("Yes", "Estimators (Section 4), protocol and metrics (Section 5), software versions and scripts (Appendix B and README) are fully specified."),
 ("Yes", "All code, the download script for the public \\texttt{ppi-python} example data (v0.2.3) and exact commands are provided in the supplementary material (anonymous); the data are not redistributed."),
 ("Yes", "Sample sizes, replications, seeds, knot counts, folds and the $t$-correction are specified in Sections 4--5; $k=4$ and 5 folds were fixed before seeing real-data results, no hyperparameter was tuned on test outcomes."),
 ("Yes", "Coverage is reported with Wilson 95\\% intervals and widths as paired ratios with standard errors over $R=2000$ (500--1000 in extensions) resamples; no multiplicity correction is applied (stated)."),
 ("Yes", "CPU only; wall-clock times of every experiment script on a shared 40-core, 250\\,GB machine are given in the README (about one hour in total); exploratory smoke tests with fewer replications were also run."),
 ("Yes", "Public, de-identified data and a purely methodological analysis; no deviations from the Code of Ethics that we are aware of."),
 ("Yes", "Section 6 notes the benefit (cheaper valid inference) and the main risk (shorter intervals presented without coverage checks overstate certainty); no direct negative application."),
 ("NA", "No models or scraped datasets with misuse risk are released."),
 ("Yes", "Assets are credited and versions given (\\texttt{ppi-python} 0.2.3, MIT licence for the code; the example \\texttt{.npz} data files carry no separate licence statement in the package or PyPI page, so we use them only for research and do not redistribute them)."),
 ("Yes", "The released code is documented in the README (environment, commands, runtimes, mapping from each table and figure to its script)."),
 ("NA", "No crowdsourcing or human-subjects research was conducted by us; the datasets are pre-existing public collections."),
 ("NA", "No human-subjects research was conducted by us."),
 ("Yes", "The research itself (design, code, experiments, analysis and drafting) was carried out by an autonomous LLM-based research agent; no LLM is part of the studied statistical methods. This is disclosed in Appendix B."),
]
assert t.count("\\answerTODO{}") == len(A) == t.count("\\justificationTODO{}"), (t.count("\\answerTODO{}"), len(A))
for ans, just in A:
    m = {"Yes": "\\answerYes{}", "No": "\\answerNo{}", "NA": "\\answerNA{}"}[ans]
    t = t.replace("\\answerTODO{}", m, 1)
    t = t.replace("\\justificationTODO{}", just, 1)
open(os.path.join(HERE, "checklist_filled.tex"), "w").write(t)
print("ok")
