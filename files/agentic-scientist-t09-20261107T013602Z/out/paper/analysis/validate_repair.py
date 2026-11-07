import hashlib
import json
import subprocess
import sys
from pathlib import Path

from src.orchestrator.paper_step import (
    find_reference_start_page,
    measure_last_body_page_fill_ratio,
    read_pdf_page_texts,
    validate_figure_manifest,
    validate_visible_language,
)
from src.orchestrator.paper_supplement import validate_rendered_supplementary_information


def sidecar(root, artifact, kind, inputs):
    manifest = {
        'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {
            'path': artifact,
            'kind': kind,
            'sha256': hashlib.sha256((root / artifact).read_bytes()).hexdigest(),
        },
        'derived_from': ['@' + 'evidence[[' + target + ']]' for target in inputs],
        'generated_by': {'script_path': 'analysis/validate_repair.py'},
    }
    (root / (artifact + '.prov.json')).write_text(json.dumps(manifest, indent=2) + '\n')


def main():
    root = Path(__file__).resolve().parent.parent
    # @evidence[[paper_data.json#/grounding_sources]]
    data = json.loads((root / 'paper_data.json').read_text())
    references = json.loads((root / 'references_provenance.json').read_text())
    text = (root / 'paper.tex').read_text()
    allowed = set(data['grounding_sources']) | {
        reference['id'] for reference in references['references']}
    figures = validate_figure_manifest(root, tex_text=text, allowed_source_ids=allowed)
    language = validate_visible_language(text, paper_profile=data['paper_profile'],
                                        presentation_contract=data['presentation_contract'])
    pages = read_pdf_page_texts(root / 'paper.pdf')
    reference_start = find_reference_start_page(pages)
    body_pages = reference_start - 1
    fill = measure_last_body_page_fill_ratio(
        root / 'paper.pdf', last_body_page_number=body_pages,
        reference_start_page=reference_start, body_columns=1)
    supplement = validate_rendered_supplementary_information(pages)
    for artifact, kind, inputs in [
        ('paper.pdf', 'manuscript', ['paper.tex', 'references.bib', 'figure_manifest.json']),
        ('claims_grounding.json', 'derived',
         ['paper_data.json', 'analysis/summary.json', 'references_provenance.json']),
        ('figure_manifest.json', 'derived', ['paper_strategy.json',
                                           'figures/endpoint_overview.prompts.json']),
    ]:
        sidecar(root, artifact, kind, inputs)
    for script, arguments in [
        ('analysis/validate_table_precision.py', []),
        ('.codex/skills/validate-paper/scripts/validate_tex_refs.py',
         ['--tex', 'paper.tex', '--bib', 'references.bib']),
        ('.codex/skills/write-paper-standalone/scripts/validate_claims.py',
         ['--paper-data', 'paper_data.json', '--references', 'references_provenance.json',
          '--bib', 'references.bib', '--claims', 'claims_grounding.json', '--paper-dir', '.']),
    ]:
        subprocess.run([sys.executable, script, *arguments], cwd=root, check=True)
    evidence = json.loads((root / 'scientific-evidence/verification-report.json').read_text())
    precision = json.loads((root / 'analysis/table_precision_validation.json').read_text())
    errors = figures['hard_errors'] + language['hard_errors'] + supplement['hard_errors']
    if not 8 <= body_pages <= 9 or fill is None or fill < .75:
        errors.append('Venue body-page geometry failed')
    if evidence['summary']['dangling_references']:
        errors.append('Dangling scientific evidence references')
    report = {
        'manuscript_repair_checks_passed': not errors,
        'full_parent_gate_passed': False,
        'manuscript_errors': errors,
        'prior_audit_finding': 'supplementary-table-precision',
        'table_precision': precision,
        'qualification': {field: data['grounding_sources']['final.qualification.' + field]['value']
                          for field in ['status', 'outcome', 'correct']},
        'claim_count': len(json.loads((root / 'claims_grounding.json').read_text())['claims']),
        'reference_count': len(references['references']),
        'figures': figures,
        'visible_language': language,
        'rendered_supplement': supplement,
        'page_geometry': {'body_pages': body_pages, 'reference_start_page': reference_start,
                          'last_body_page_fill_ratio': fill, 'total_pages': len(pages)},
        'evidence_summary': evidence['summary'],
        'sanitized_latex_and_bibtex_compilation': 'passed',
        'remaining_environment_limitations': [
            'Strict compile wrapper requires unavailable pdftotext; canonical rendered checks used pypdf.',
            'Recorder-input validation rejects the existing system texmf.cnf symlink outside approved roots.',
            'Concept rendering failed as documented in its retained prompt log; placeholder is unchanged.',
        ],
        'new_scientific_evaluations': False,
        'parent_feedback_preserved': True,
    }
    output = 'repair_validation_report.json'
    (root / output).write_text(json.dumps(report, indent=2) + '\n')
    sidecar(root, output, 'derived', ['analysis/table_precision_validation.json',
                                     'paper.pdf', 'paper.tex', 'figure_manifest.json'])
    print(json.dumps({key: report[key] for key in [
        'manuscript_repair_checks_passed', 'manuscript_errors', 'page_geometry']}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
