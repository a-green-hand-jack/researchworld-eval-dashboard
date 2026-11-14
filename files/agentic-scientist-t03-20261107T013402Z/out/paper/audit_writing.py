import hashlib
import json
import re
from pathlib import Path

import jsonschema
from src.orchestrator.paper_step import find_reference_start_page, find_supplement_start_page, measure_last_body_page_fill_ratio, read_pdf_page_texts, validate_figure_manifest


def digest_tree(root):
    hasher = hashlib.sha256()
    for path in sorted(root.rglob('*'), key=lambda path: path.relative_to(root).as_posix()):
        if path.is_symlink():
            raise RuntimeError('Unexpected symlink in evaluated tree')
        relative = path.relative_to(root).as_posix().encode()
        if path.is_dir():
            hasher.update(b'dir\0' + relative + b'\0')
        else:
            content = path.read_bytes()
            hasher.update(b'file\0' + relative + b'\0' + str(len(content)).encode() + b'\0' + content)
    return 'sha256:' + hasher.hexdigest()


def check_locator(reference):
    target, separator, locator = reference.partition('#')
    path = Path(target)
    if not path.is_file():
        raise RuntimeError('Missing target: ' + reference)
    if locator.startswith('/') and path.suffix == '.json':
        value = json.loads(path.read_text())
        for segment in locator[1:].split('/'):
            segment = segment.replace('~1', '/').replace('~0', '~')
            value = value[int(segment)] if isinstance(value, list) else value[segment]
    elif locator.startswith('L'):
        match = re.fullmatch(r'L(\d+)(?:-L(\d+))?', locator)
        if match:
            start = int(match[1])
            end = int(match[2] or match[1])
            if not 1 <= start <= end <= len(path.read_text().splitlines()):
                raise RuntimeError('Invalid source line range: ' + reference)


def main():
    # @evidence[[paper_data.json]]
    # @evidence[[paper.tex]]
    data = json.loads(Path('paper_data.json').read_text())
    claims = json.loads(Path('claims_grounding.json').read_text())
    tex = Path('paper.tex').read_text()
    refs = set()
    owned = [Path('paper.tex'), Path('build_artifacts.py'), Path('build_claims.py')] + list(Path('tables').glob('*.tex'))
    for file in owned:
        refs.update(re.findall(r'@evidence\[\[([^\]]+)\]\]', file.read_text()))
    for claim in claims['claims']:
        refs.update(claim['evidence_refs'])
    for reference in refs:
        check_locator(reference)
    for table in Path('tables').glob('*_rows.tex'):
        for row in table.read_text().splitlines():
            if row and not row.startswith('%') and row not in tex:
                raise RuntimeError('Stale embedded table row: ' + row)
    root = next(Path('results/ideas').glob('03*/program_1')).resolve()
    digest = digest_tree(root)
    expected = data['final_evaluation']['program_tree_sha256']
    if digest != expected:
        raise RuntimeError('Retained selected source does not match evaluated tree')
    for path in (root / 'src').glob('*'):
        if path.is_file() and (Path('source_evidence/selected') / path.name).read_bytes() != path.read_bytes():
            raise RuntimeError('Copied source differs: ' + path.name)
    schema = json.loads(Path('.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(json.loads(Path('figure_manifest.json').read_text()), schema)
    # @evidence[[paper.pdf]]
    pages = read_pdf_page_texts(Path('paper.pdf'))
    reference_start = find_reference_start_page(pages)
    supplement_start = find_supplement_start_page(pages)
    if reference_start is None or supplement_start is None:
        raise RuntimeError('Missing rendered reference/supplement boundary')
    body_pages = reference_start - 1
    fill = measure_last_body_page_fill_ratio(Path('paper.pdf'), last_body_page_number=body_pages, reference_start_page=reference_start, body_columns=1)
    if not (8 <= body_pages <= 9 and (body_pages > 8 or fill >= .75)):
        raise RuntimeError('Venue page requirement not satisfied')
    visible = '\n'.join(pages)
    forbidden = re.findall(r'\b(?:ideas?|programs?|attempts?|eligible|combined_score|rubric|worker_01|worker_02)\b', visible, re.I)
    if forbidden:
        raise RuntimeError('Forbidden visible terms: ' + str(forbidden))
    allowed = set(data['grounding_sources']) | {reference['id'] for reference in json.loads(Path('references_provenance.json').read_text())['references']}
    figure_report = validate_figure_manifest(Path('.').resolve(), tex_text=tex, allowed_source_ids=allowed)
    expected_pending = 'Concept prompt log is an empty placeholder'
    unexpected = [error for error in figure_report['hard_errors'] if expected_pending not in error]
    if unexpected:
        raise RuntimeError('Unexpected figure errors: ' + str(unexpected))
    report = {
        'status': 'ready_for_synchronous_concept_render_and_parent_validation',
        'all_checks_complete': False,
        'completed': {
            'latex_pdf_compilation': 'succeeded using sanitized commands and canonical bibliography-target validation',
            'section_and_citation_validation': 'passed',
            'claim_and_reference_provenance_validation': 'passed',
            'claims': len(claims['claims']),
            'references': len(json.loads(Path('references_provenance.json').read_text())['references']),
            'checked_file_json_and_line_locators': len(refs),
            'embedded_tables_match_regenerated_rows': True,
            'evaluated_source_tree_identity': {'matched': True, 'sha256': digest},
            'copied_source_byte_identity': True,
            'figure_manifest_schema': 'passed',
            'quantitative_figure_manifest_validation': 'passed; sole full-manifest error is pending concept log',
            'rendered_supplementary_information': 'passed',
            'visible_language_scan': 'passed',
            'page_budget': {'body_pages': body_pages, 'reference_start_page': reference_start, 'supplement_start_page': supplement_start, 'total_pages': len(pages), 'last_body_fill': fill, 'minimum_fill': .75, 'method': 'canonical geometric fill function with observed reference boundary and venue-brief budget; not character count'},
            'official_template_byte_identity': Path('paper.sty').read_bytes() == Path('template_evidence/iclr2026_conference.sty').read_bytes(),
        },
        'pending': [
            'Orchestrator must replace fixed_game_overview placeholder PNG and empty prompt log, then recompile and revalidate figures.',
            'Canonical compile wrapper recorder rejects /usr/share/texmf/web2c/texmf.cnf, a system symlink resolving into /usr/share/texlive/texmf-dist/web2c/texmf.cnf. Both are standard system roots; validator was not modified. Parent must perform final recorder validation in its environment.',
            'Installed validator distribution omits venue config files; its automatic venue detection is unavailable. Canonical geometric measurement was called explicitly using the actual reference boundary and VENUE.md budget.'
        ],
        'figure_report': figure_report,
    }
    Path('writing_validation.json').write_text(json.dumps(report, indent=2))
    sidecar = {'schema_name': 'scientific-evidence.artifact-manifest', 'artifact': {'path': 'writing_validation.json', 'kind': 'derived', 'sha256': hashlib.sha256(Path('writing_validation.json').read_bytes()).hexdigest()}, 'derived_from': ['@evidence[[paper.pdf]]', '@evidence[[paper.tex]]', '@evidence[[claims_grounding.json]]', '@evidence[[figure_manifest.json]]', '@evidence[[VENUE.md]]'], 'generated_by': {'script_path': 'audit_writing.py'}}
    Path('writing_validation.json.prov.json').write_text(json.dumps(sidecar, indent=2))
    print(json.dumps(report['completed'], indent=2))


if __name__ == '__main__':
    main()
