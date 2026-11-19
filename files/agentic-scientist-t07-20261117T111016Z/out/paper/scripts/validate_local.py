"""Supplement canonical checks with explicit rendered and JSON-locator audits.

This does not replace the parent orchestrator's authoritative venue validation.
@evidence[[paper.tex]]
@evidence[[analysis/paper_statistics.json]]
"""

import datetime
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import fitz
import jsonschema


ROOT = Path(__file__).resolve().parents[1]


def check_pointer(reference):
    prefix = '@' + 'evidence' + '[' * 2
    inner = reference.removeprefix(prefix).removesuffix(']' * 2)
    target, separator, locator = inner.partition('#')
    path = ROOT / target
    if not path.is_file():
        raise ValueError('Missing local evidence: ' + reference)
    if separator and locator.startswith('/') and path.suffix == '.json':
        value = json.loads(path.read_text())
        for component in locator[1:].split('/'):
            component = component.replace('~1', '/').replace('~0', '~')
            value = value[int(component)] if isinstance(value, list) else value[component]
    if separator and re.fullmatch(r'L\d+', locator):
        assert 1 <= int(locator[1:]) <= len(path.read_text().splitlines()), reference


def main():
    commands = [
        ['python', '.codex/skills/validate-paper/scripts/validate_tex_refs.py', '--tex', 'paper.tex', '--bib', 'references.bib'],
        [sys.executable, '.codex/skills/write-paper-standalone/scripts/validate_claims.py', '--paper-data', 'paper_data.json', '--references', 'references_provenance.json', '--bib', 'references.bib', '--claims', 'claims_grounding.json', '--paper-dir', '.'],
        ['python', '.codex/skills/validate-paper/scripts/validate_rendered_si.py', '--pdf', 'paper.pdf'],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)
    figure_schema = json.loads((ROOT / '.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    figure_manifest = json.loads((ROOT / 'figure_manifest.json').read_text())
    jsonschema.validate(figure_manifest, figure_schema)
    sidecar_schema = json.loads((ROOT / 'scientific-evidence/schemas/artifact-manifest.schema.json').read_text())
    for path in ROOT.rglob('*.prov.json'):
        jsonschema.validate(json.loads(path.read_text()), sidecar_schema)
    texts = [ROOT / 'paper.tex', *list((ROOT / 'scripts').glob('*.py')), *list((ROOT / 'tables').glob('*.tex'))]
    checked = 0
    for path in texts:
        for reference in re.findall(r'@evidence\[\[[^\]]+\]\]', path.read_text()):
            check_pointer(reference)
            checked += 1
    manuscript = (ROOT / 'paper.tex').read_text()
    for table in ['case_budget', 'seeds']:
        embedded = manuscript.split('% BEGIN GENERATED ' + table + '\n')[1].split('% END GENERATED ' + table)[0]
        assert embedded.strip() == (ROOT / ('tables/' + table + '.tex')).read_text().strip()
    claims = json.loads((ROOT / 'claims_grounding.json').read_text())['claims']
    for claim in claims:
        for reference in claim.get('evidence_refs', []):
            check_pointer(reference)
    registry = json.loads((ROOT / 'paper_data.json').read_text())
    for source in ['final.qualification.status', 'final.qualification.outcome']:
        assert source in registry['grounding_sources']
    reference_records = json.loads((ROOT / 'references_provenance.json').read_text())['references']
    cited = set()
    for group in re.findall(r'\\cite\w*\{([^}]+)\}', (ROOT / 'paper.tex').read_text()):
        cited.update(key.strip() for key in group.split(','))
    assert cited == {record['citation_key'] for record in reference_records}
    assert 25 <= len(cited) <= 30
    specifications = json.loads((ROOT / 'paper_strategy.json').read_text())['figure_specs']
    figures = {figure['figure_id']: figure for figure in figure_manifest['figures']}
    for spec in specifications:
        actual = figures[spec['figure_id']]
        assert actual['figure_type'] == spec['figure_type']
        assert actual['n_panels'] <= spec['max_panels']
        assert max(actual['categories_per_panel']) <= spec['max_categories_per_panel']
        assert max(actual['series_per_panel']) <= spec['max_series_per_panel']
    module_path = ROOT / '.codex/skills/validate-paper/scripts/validate_compile_inputs.py'
    spec = importlib.util.spec_from_file_location('compile_guard', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    roots = [path.resolve() for path in module.LATEX_SYSTEM_INPUT_ROOTS]
    safe_inputs = set()
    for line in (ROOT / 'paper.fls').read_text().splitlines():
        if not line.startswith('INPUT '):
            continue
        path = Path(line.removeprefix('INPUT '))
        if not path.is_absolute():
            path = ROOT / path
        resolved = path.resolve()
        assert resolved.is_relative_to(ROOT) or any(resolved.is_relative_to(root) for root in roots), str(path)
        assert not resolved.is_relative_to(ROOT / '.codex'), str(path)
        safe_inputs.add(str(resolved))
    document = fitz.open(ROOT / 'paper.pdf')
    pages = [page.get_text() for page in document]
    reference_page = next(index for index, text in enumerate(pages) if re.search(r'(?m)^REFERENCES$', text))
    supplement_page = next(index for index, text in enumerate(pages) if 'SUPPLEMENTARY INFORMATION' in text)
    last_body = document[reference_page - 1]
    boxes = []
    for block in last_body.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            left, top, right, bottom = line['bbox']
            if left >= 105 and right <= 507 and 70 < top < 730 and bottom < 735:
                boxes.append((top, bottom))
    for image in last_body.get_images():
        boxes.extend((box.y0, box.y1) for box in last_body.get_image_rects(image[0]))
    geometric_fill = (max(box[1] for box in boxes) - min(box[0] for box in boxes)) / (9 * 72)
    assert reference_page in [8, 9]
    assert reference_page != 8 or geometric_fill >= 0.75
    cleaned = '\n'.join(pages)
    cleaned = re.sub(r'source_evidence/selected/src/\s*program\.py', '', cleaned)
    forbidden = r'\b(?:idea|ideas|program|programs|attempt|attempts|eligible|worker_01|worker_02|combined_score|rubric)\b'
    assert not re.search(forbidden, cleaned, re.I)
    report = dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  checks_status='passed_local_checks', body_pages=reference_page,
                  total_pages=len(document), references_start_page=reference_page + 1,
                  supplementary_start_page=supplement_page + 1,
                  local_last_body_page_geometric_fill=geometric_fill,
                  citation_count=len(cited), claim_count=len(claims),
                  locator_checks=checked, safe_resolved_tex_input_count=len(safe_inputs),
                  canonical_limitations=[
                      'Canonical figure CLI imports unavailable src.orchestrator; canonical figure JSON Schema and declared strategy density limits checked directly.',
                      'Canonical compile recorder rejects Debian /usr/share/texmf/web2c/texmf.cnf symlink resolving inside separately approved /usr/share/texlive. Sanitized compile and canonical bibliography/rendered-SI checks run separately; all resolved input paths checked against the union of approved roots.',
                      'Rendered page geometry is a local cross-check, not the parent orchestrator authoritative venue report.',
                      'Concept overview remains orchestrator-owned; its rendered asset and provenance are preserved during repair.'])
    (ROOT / 'paper_checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
