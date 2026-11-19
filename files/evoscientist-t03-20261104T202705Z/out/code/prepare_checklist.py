"""Fill the unmodified official checklist questions/guidelines, retaining all 16."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent
s=(root/'template/checklist.tex').read_text()
s=re.sub(r'%%% BEGIN INSTRUCTIONS %%%.*?%%% END INSTRUCTIONS %%%','',s,flags=re.S)
answers=[
('Yes',r'Abstract, Introduction, and Sections 3--6 delimit the contribution to measured recovery of fixed empirical games. German reference agreement and descriptive uncertainty are explicitly distinguished from exact fidelity and deployment safety.'),
('Yes',r'Section 5 discusses sampling, reference, background, model, computational, novelty, and safety limits; weak fits and negative or inconclusive outcomes are retained.'),
('NA',r'No new theoretical theorem is claimed. Section 3 defines the estimators and reports standard telescoping and bounded-mean calculations with their sampling assumptions, not a novel certification guarantee.'),
('Yes',r'Sections 3--4 and Appendices A--G specify the game, splits, preprocessing, models, paths, costs, seeds, analysis, and commands. The accompanying code and measured arrays reproduce the tables and figures; post-review manifest-preservation tests cover the fresh command sequence.'),
('Yes',r'The supplement provides experimental and analysis code, derived result arrays, version inventory, and acquisition scripts for public sources. Raw datasets are not redistributed while Pima/Census redistribution terms remain unresolved; the README documents acquisition and hashes.'),
('Yes',r'Section 4 and Appendix A disclose fixed hyperparameters, exact partitions and labels, train-only preprocessing, and internal MLP early stopping. No test-driven training tuning was performed.'),
('Yes',r'Section 3 and Appendix B define 2,000 paired instance-cluster percentile bootstrap replicates and the reported 63-contrast simultaneous descriptive bands. Fixed seeds, dependent repetition pairs, boundary degeneracy, ACS sampling limitations, and lack of finite-sample certification are explicit.'),
('No',r'Appendix G and resource tables report per-cell CPU and wall timers, thread/worker settings, logical costs, successful-campaign totals, and a post-experiment host inventory. Historical allocation, peak memory, and complete failed-run overhead were not measured, so a fully instrumented resource record is unavailable.'),
('No',r'The official ethics guidance was reviewed, and the work documents privacy, representation, intended-use, and societal-risk boundaries. Full compliance cannot be asserted while the detailed Pima/Census asset terms remain unresolved; raw data and fitted model files are withheld from the supplementary archive.'),
('Yes',r'Section 5 discusses potential benefit from explicit approximation auditing and harm from false confidence in credit or medical decisions. Exact recovery is not presented as safety, fairness, causal validity, or authorization for consequential deployment.'),
('NA',r'The supplement releases audit code and derived numerical results, not a high-risk generative model, scraped personal dataset, or deployment service. Intended-use limitations and the exclusion of raw data/fitted model files are documented in the README.'),
('No',r'Original sources and software versions are credited, German CC BY 4.0 is verified, and Folktables software licensing is distinguished from Census data. OpenML lists Pima only as Public, and detailed Census terms were not established; DATA\_LICENSES.md records this uncertainty and the downloader-only policy.'),
('Yes',r'The README, ARTIFACT\_MAP.md, scripts, configs, input hashes, derived arrays, and environment inventory document the new computational audit assets. No new human-subject dataset is collected, and the original-code license does not relicense third-party data or templates.'),
('NA',r'No crowdsourcing, participant recruitment, compensation, direct human interaction, or new human-subject experiment was performed. The study reuses existing public tabular records for a computational audit.'),
('NA',r'No participants were recruited or contacted, and no new human-subject intervention was conducted. No institutional IRB approval or formal exemption determination was obtained or claimed for this reuse of existing public records.'),
('Yes',r'The final reproducibility appendix discloses that an LLM-based assistant selected the protocol, implemented and ran experiments, analyzed measured artifacts, drafted the paper, and performed automated self-review. It explicitly notes the absence of independent human verification during this unattended run.')
]
assert len(re.findall(r'\\answerTODO\{\}',s))==16
for ans,why in answers:
    s=s.replace(r'\answerTODO{}',f'\\answer{ans}{{}}',1)
    s=s.replace(r'\justificationTODO{}',why,1)
s=s.replace(' % Replace by \\answerYes{}, \\answerNo{}, or \\answerNA{}.','')
assert 'TODO' not in s
(root/'checklist_filled.tex').write_text(s)
print('16 official checklist answers filled; questions and guidelines retained.')
