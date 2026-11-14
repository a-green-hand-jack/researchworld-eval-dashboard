import json
import re
from pathlib import Path


manuscript = Path('paper.tex').read_text()
claims = []
for paragraph in re.split(r'\n\s*\n', manuscript):
    evidence = re.findall(r'@evidence\[\[([^\]]+)\]\]', paragraph)
    citations = sorted(set(key.strip() for block in re.findall(r'\\cite\w*\{([^}]+)\}', paragraph)
                           for key in block.split(',')))
    if not evidence and not citations:
        continue
    content = re.sub(r'(?m)%.*$', '', paragraph).strip()
    if not content:
        continue
    source_ids = []
    if any('qualification' in target for target in evidence):
        source_ids.extend(['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct'])
    if any('metrics' in target for target in evidence):
        source_ids.extend(['final.metric.combined_score', 'final.metric.combined_score_ci_low',
                           'final.metric.combined_score_ci_high', 'final.metric.reference_mass',
                           'final.metric.group_coverage_error', 'final.metric.marginal_coverage_error',
                           'final.metric.global_ilr_score_gap', 'final.metric.control_pass_fraction',
                           'final.metric.constant_control_score', 'final.metric.permuted_control_score'])
    if evidence and not source_ids:
        source_ids.append('final.evidence.episodes')
    source_ids.extend('ref.' + key for key in citations)
    claims.append(dict(claim=content, source_ids=sorted(set(source_ids)), citation_keys=citations,
                       evidence_refs=evidence,
                       support_scope=('Implementation/protocol facts require the listed readable source files; '
                                      'the episode ID links the evaluation context, not every code detail.'
                                      if any('source_evidence' in target for target in evidence)
                                      else 'Frozen final observations or directly consulted references.')))

claims.extend([
    dict(claim='The complete selected procedure, not an isolated stump component, is the object supported by the final comparison.',
         source_ids=['final.evidence.episodes'], citation_keys=[],
         evidence_refs=['source_evidence/scale_learner.py#L158-L225']),
    dict(claim='Search scores are not final results; the original learned ridge scale has no matched repeated-final comparator; missing component diagnostics prevent causal attribution.',
         source_ids=['final.evidence.episodes'], citation_keys=[]),
    dict(claim='No failed final qualification is recorded; unspecified gate diagnostics remain unknown.',
         source_ids=['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct'], citation_keys=[]),
    dict(claim='Every supplementary utility and group/mass table entry is an arithmetic mean or sample standard deviation of the matched final seed records.',
         source_ids=['final.evidence.episodes'], citation_keys=[],
         evidence_refs=['analysis_summary.json#/cases', 'tables/condition_utility.tex', 'tables/group_mass.tex'])
])
Path('claims_grounding.json').write_text(json.dumps(dict(claims=claims), indent=2) + '\n')
print('Wrote', len(claims), 'claim mappings')
