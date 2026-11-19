"""Preserve official 2026 questions and guidelines; fill all sixteen answers."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/'paper/vendor/checklist.tex').read_text()
src=src[:src.index('%%% BEGIN INSTRUCTIONS %%%')]+src[src.index('%%% END INSTRUCTIONS %%%')+len('%%% END INSTRUCTIONS %%%'):]
answers=[
 ('Yes',r'Sections 1 and 5 distinguish exact counts, bounded counts, uncertainty, and the fixed-schedule scope.'),
 ('Yes',r'Section 6 discusses model assumptions, dataset coverage, dependence, selection, judge bias, and offline access.'),
 ('Yes',r'Theorem 1 states the assumptions; Appendix A gives the complete maximum-principle and interpolation proofs, plus the curvature-bound proof.'),
 ('Yes',r'Sections 3--4 and Appendix C specify the objective, eligibility, endpoints, controls, seeds, resampling, and exact reproduction commands.'),
 ('Yes',r'The accompanying artifact includes all code and generated results. Frozen public data URLs, full checksums, dependency versions, and acquisition scripts are supplied; raw data are downloaded separately.'),
 ('Yes',r'Sections 3--4 specify all settings; no hyperparameter search, training/test split, or fitted prediction benchmark is used.'),
 ('Yes',r'Sections 3.3 and 5 explain question-cluster/record/game bootstrap intervals and conditional Monte Carlo Wilson intervals. Deterministic finite-dataset attack counts have no artificial error bars; descriptive and selection limitations are stated.'),
 ('Yes',r'Section 4 and Appendix C report CPU model, thread count, wall times, memory, and absence of GPU use; the research log records preliminary work.'),
 ('Yes',r'The official ethics guidelines were reviewed. Section 6 describes offline use of public licensed data, no participant contact or live manipulation, and exclusion of conversations from the release.'),
 ('Yes',r'Section 6 discusses more cautious leaderboard use and potential misuse of edit-selection code.'),
 ('NA',r'No new high-risk model or scraped dataset is released. The artifact is an offline audit of existing public data; Section 6 states its misuse limitations and release scope.'),
 ('Yes',r'Appendix C and the data manifest credit creators, preserve exact snapshots and dataset cards, and list Apache-2.0 and CC-BY-4.0 terms. The official template is preserved unchanged.'),
 ('Yes',r'The new code, result files, numerical witnesses, README, and display provenance map are included; data downloads remain separate and code licensing is explicit.'),
 ('NA',r'No new crowdsourcing or human-participant interaction was conducted. Existing expert and crowd datasets are used for secondary analysis and credited in Section 4.'),
 ('NA',r'No participants were recruited, contacted, or assigned interventions. Only public historical records are analyzed; we do not claim a new IRB approval.'),
 ('Yes',r'Section 6 explicitly discloses that an OpenAI Codex assistant developed the method and code, ran the study, inspected results, and drafted the manuscript. LLM generation is not an experimental measurement.'),
]
assert src.count(r'\answerTODO{}')==len(answers)
for answer,justification in answers:
    src=src.replace(r'\answerTODO{}',r'\answer'+answer+'{}',1)
    src=src.replace(r'\justificationTODO{}',justification,1)
src=re.sub(r' % Replace by .*','',src)
(ROOT/'paper/checklist_filled.tex').write_text(src)

