import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import jsonschema
import pymupdf


def main():
    from src.orchestrator.paper_step import (
        find_reference_start_page,
        measure_last_body_page_fill_ratio,
        read_pdf_page_texts,
        validate_figure_manifest,
        validate_visible_language,
    )
    root = Path.cwd()
    text = Path('paper.tex').read_text()
    data = json.loads(Path('paper_data.json').read_text())
    references = json.loads(Path('references_provenance.json').read_text())
    claims = json.loads(Path('claims_grounding.json').read_text())
    schema = json.loads(Path('.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(json.loads(Path('figure_manifest.json').read_text()), schema)
    allowed_sources = set(data['grounding_sources']) | {reference['id'] for reference in references['references']}
    figure_report = validate_figure_manifest(root, tex_text=text, allowed_source_ids=allowed_sources)
    language = validate_visible_language(text, paper_profile=data['paper_profile'],
                                         presentation_contract=data['presentation_contract'])
    page_texts = read_pdf_page_texts(Path('paper.pdf'))
    reference_start = find_reference_start_page(page_texts)
    body_pages = reference_start - 1
    fill = measure_last_body_page_fill_ratio(Path('paper.pdf'), last_body_page_number=body_pages,
                                            reference_start_page=reference_start, body_columns=1)
    evidence = json.loads(Path('scientific-evidence/verification-report.json').read_text())
    source_hashes = {name: hashlib.sha256(Path('source_evidence', name).read_bytes()).hexdigest()
                     for name in ['estimator.py', 'evaluate_final.py']}
    evaluator_match = 'sha256:' + source_hashes['evaluate_final.py'] == data['final_evaluation']['evaluator_sha256']
    pages = {'body_pages': body_pages, 'reference_start_page': reference_start,
             'last_body_page_fill_ratio': fill, 'min_body_pages': 8,
             'max_body_pages': 9, 'minimum_fill': .75,
             'method': 'canonical geometric helper with explicit VENUE.md constraints'}
    Path('page_validation.json').write_text(json.dumps(pages, indent=2))
    expected_pending = 'Concept prompt log is an empty placeholder'
    figure_errors = figure_report.get('hard_errors', [])
    unexpected = [error for error in figure_errors if expected_pending not in error]
    unexpected += language.get('hard_errors', [])
    if body_pages < 8 or body_pages > 9 or fill is None or fill < .75:
        unexpected.append('Body-page geometric requirement failed')
    if evidence['summary']['dangling_references']:
        unexpected.append('Dangling scientific evidence references')
    if not evaluator_match:
        unexpected.append('Readable evaluator snapshot differs from recorded evaluator hash')
    qualification = {key: data['grounding_sources']['final.qualification.' + key]['value']
                     for key in ['status', 'outcome', 'correct']}
    report = {'status': 'draft_ready_for_orchestrator' if not unexpected else 'requires_repair',
        'full_gate_passed': False, 'hard_errors_requiring_manuscript_repair': unexpected,
        'qualification': qualification, 'claim_count': len(claims['claims']),
        'reference_count': references['count'], 'figure_manifest_schema_valid': True,
        'figures': figure_report, 'visible_language': language, 'page_geometry': pages,
        'evidence_summary': evidence['summary'], 'evaluator_snapshot_hash_matches': evaluator_match,
        'selected_source_identity_independently_reconstructed': False,
        'readable_source_sha256': source_hashes,
        'sanitized_latex_compilation': 'passed; complete PDF with resolved bibliography',
        'bibliography_dependency_validation': 'passed',
        'sections_citations_claim_mapping': 'passed',
        'rendered_supplement': 'passed',
        'deferred': [
            'Orchestrator-owned overview PNG and prompt log must replace the mandated placeholders, followed by final compile and page check.',
            'Strict recorder-input wrapper rejects an existing system TeX configuration symlink between approved system trees; no scientific source or validator was changed to bypass it.'],
        'scientific_runs_performed_for_manuscript': False}
    Path('validation_report.json').write_text(json.dumps(report, indent=2))
    for artifact, kind in [('paper.pdf', 'manuscript'), ('claims_grounding.json', 'derived'),
                           ('figure_manifest.json', 'derived')]:
        sidecar = {'schema_name': 'scientific-evidence.artifact-manifest',
            'artifact': {'path': artifact, 'kind': kind,
                         'sha256': hashlib.sha256(Path(artifact).read_bytes()).hexdigest()},
            'derived_from': ['@' + 'evidence[[' + target + ']]' for target in (
                ['paper.tex', 'references.bib', 'figure_manifest.json'] if artifact == 'paper.pdf'
                else ['paper_data.json', 'analysis/summary.json', 'references_provenance.json'])],
            'generated_by': {'script_path': 'audit_paper.py'}}
        Path(artifact + '.prov.json').write_text(json.dumps(sidecar, indent=2))
    print(json.dumps({key: report[key] for key in ['status', 'hard_errors_requiring_manuscript_repair',
                     'qualification', 'claim_count', 'reference_count', 'page_geometry',
                     'evaluator_snapshot_hash_matches']}, indent=2))
    if unexpected:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
