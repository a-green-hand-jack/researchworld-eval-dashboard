"""Bounded citation enrichment: @evidence[[references.openalex.json]]."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
DIRECTORY = ROOT / 'literature/Henderson2024'
NOW = datetime.now(timezone.utc).isoformat()
KEY = 'Henderson2024'
QUERY = 'split-conformal multivariate regression ellipsoidal prediction regions residual covariance'
abstract_page = BeautifulSoup((DIRECTORY / 'abstract_page.html').read_text(), 'html.parser')
metadata = {}
for element in abstract_page.select('meta[name^="citation_"]'):
    metadata.setdefault(element['name'], []).append(element['content'])
title = metadata['citation_title'][0]
assert metadata['citation_arxiv_id'] == ['2409.18508']
assert title == 'Adaptive inference with random ellipsoids through Conformal Conditional Linear Expectation'
authors = metadata['citation_author']
year = metadata['citation_date'][0].split('/')[0]
revision = datetime.strptime(metadata['citation_online_date'][0], '%Y/%m/%d').strftime('%d %B %Y').lstrip('0')
source_url = 'https://arxiv.org/html/2409.18508v2'
source = BeautifulSoup((DIRECTORY / 'source.html').read_text(), 'html.parser')
sections = ['S2', 'S3.SS2', 'S3.SS3', 'S3.SS5']
excerpts = []
for section_id in sections:
    section = source.find(id=section_id)
    assert section is not None
    for formula in section.find_all('math'):
        formula.replace_with(' ' + formula.get('alttext', '[math]') + ' ')
    for reference in section.select('.ltx_ref'):
        reference.replace_with('[cross-reference]')
    excerpts.append(section_id + '\n' + section.get_text(' ', strip=True))
(DIRECTORY / 'method_excerpt.txt').write_text('\n\n'.join(excerpts) + '\n')
reading_scope = 'Inspected bibliographic metadata, abstract, split-inference setup, joint Mahalanobis construction, first ellipsoid theorem and interpretation, and adjusted-score ellipsoid (Sections 2, 3.2, 3.3, 3.5). No full-paper, proof, bibliography, or citation-chain review claimed.'
reading = {
    'title': title,
    'authors': authors,
    'abstract': metadata['citation_abstract'][0],
    'reading_scope': reading_scope,
    'source_url': source_url,
    'source_version': '2409.18508v2',
    'original_submission_date': metadata['citation_date'][0],
    'version_revision_date': metadata['citation_online_date'][0],
    'inspected_sections': sections,
    'construction_support': {
        'joint_covariate_residual_score': 'Section 3.2, equations (8)-(12). Covariance includes the trial residual symmetrically to preserve exchangeability; this is not the studied training-frozen score.',
        'covariate_dependent_center_and_radius': 'Section 3.3, Theorem 3.1, equations (24)-(29). The shape is a covariance Schur complement, the residual center is affine in covariates, and the radius depends on covariate Mahalanobis distance.',
        'scope': 'General multivariate regression; no claim of ILR identity, evaluated superiority, simplex-volume guarantees, or conditional coverage.'
    },
    'no_citation_chaining': True,
    'retrieved_at': NOW,
}
(DIRECTORY / 'reading.json').write_text(json.dumps(reading, indent=2) + '\n')
record = {
    'id': 'ref.' + KEY,
    'citation_key': KEY,
    'paper_id': 'arxiv:2409.18508',
    'title': title,
    'year': int(year),
    'query': QUERY,
    'retrieved_at': NOW,
    'source_url': source_url,
    'reading_path': 'literature/Henderson2024/reading.json',
    'reading_scope': reading_scope,
    'candidate_provenance': 'references.openalex.json: ref.openalex.W4403048436',
}
provenance_path = ROOT / 'references_provenance.json'
provenance = json.loads(provenance_path.read_text())
provenance['references'] = [entry for entry in provenance['references'] if entry['citation_key'] != KEY] + [record]
provenance['count'] = len(provenance['references'])
provenance['generated_at'] = NOW
if QUERY not in provenance['queries']:
    provenance['queries'].append(QUERY)
provenance_path.write_text(json.dumps(provenance, indent=2) + '\n')
bibliography_path = ROOT / 'references.bib'
bibliography = bibliography_path.read_text()
if '{' + KEY + ',' not in bibliography:
    author_field = ' and '.join(authors)
    bibliography += ('\n@article{' + KEY + ',\n'
        '  author = {' + author_field + '},\n'
        '  title = {{' + title + '}},\n'
        '  year = {' + year + '},\n'
        '  journal = {arXiv preprint arXiv:2409.18508},\n'
        '  note = {Version 2, revised ' + revision + '},\n'
        '  url = {https://arxiv.org/abs/2409.18508v2},\n}\n')
    bibliography_path.write_text(bibliography)
for artifact_name, inputs in {
    'method_excerpt.txt': ['literature/Henderson2024/source.html'],
    'reading.json': ['literature/Henderson2024/abstract_page.html', 'literature/Henderson2024/method_excerpt.txt', 'references.openalex.json'],
}.items():
    artifact = DIRECTORY / artifact_name
    sidecar = {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': str(artifact.relative_to(ROOT)), 'kind': 'derived', 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()},
        'derived_from': ['@' + 'evidence[[' + target + ']]' for target in inputs],
        'generated_by': {'script_path': 'enrich_joint_region.py'},
        'notes': 'One directly inspected literature comparator; no new experimental result.',
    }
    Path(str(artifact) + '.prov.json').write_text(json.dumps(sidecar, indent=2) + '\n')
print('Retained one verified joint-region citation; bibliography count:', provenance['count'])
for artifact_name, inputs in {
    'paper.tex': ['paper_data.json', 'references_provenance.json', 'source_evidence/adaptive.py', 'source_evidence/evaluate_final.py', 'literature/Henderson2024/reading.json'],
    'references.bib': ['references_provenance.json', 'finalize_references.py', 'enrich_joint_region.py'],
    'references_provenance.json': ['literature/reading_report.txt', 'finalize_references.py', 'enrich_joint_region.py', 'literature/Henderson2024/reading.json'],
}.items():
    artifact = ROOT / artifact_name
    sidecar = {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': artifact_name, 'kind': 'manuscript' if artifact_name == 'paper.tex' else 'derived', 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()},
        'derived_from': ['@' + 'evidence[[' + target + ']]' for target in inputs],
        'generated_by': {'script_path': 'enrich_joint_region.py'},
        'notes': 'Refresh of inspected input provenance for targeted citation enrichment; no numerical evidence changed.',
    }
    Path(str(artifact) + '.prov.json').write_text(json.dumps(sidecar, indent=2) + '\n')
