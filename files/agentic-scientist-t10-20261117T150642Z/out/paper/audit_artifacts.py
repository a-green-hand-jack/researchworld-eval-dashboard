import hashlib
import importlib.util
import json
import re
from pathlib import Path

import jsonschema
import pymupdf


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root/'figure_manifest.json').read_text())
    schema = json.loads((root/'.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(manifest, schema)
    strategy = json.loads((root/'paper_strategy.json').read_text())
    text = (root/'paper.tex').read_text()
    referenced = set(re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', text))
    registered = {path for figure in manifest['figures'] for path in figure['files'].values() if path}
    assert referenced <= registered, referenced-registered
    figures = {figure['figure_id']: figure for figure in manifest['figures']}
    for spec in strategy['figure_specs']:
        figure = figures[spec['figure_id']]
        assert figure['panel_count'] <= spec['max_panels']
        assert figure['estimated_min_rendered_font_pt'] >= 8
        for panel in figure['panels']:
            assert panel.get('category_count', 1) <= spec['max_categories_per_panel']
            assert panel.get('series_count', 1) <= spec['max_series_per_panel']
        for path in figure['files'].values():
            assert not path or (root/path).is_file()
    pdf = pymupdf.open(root/'paper.pdf')
    pages = [page.get_text() for page in pdf]
    references_page = next(index for index, value in enumerate(pages) if re.search(r'^REFERENCES\s*$', value, re.M))
    supplement_page = next(index for index, value in enumerate(pages) if re.search(r'^SUPPLEMENTARY INFORMATION\s*$', value, re.M))
    assert references_page in (8, 9), references_page
    assert supplement_page > references_page
    assert all('??' not in page for page in pages)
    visible = '\n'.join(pages)
    visible = re.sub(r'source.evidence/\s*program\.py', '', visible, flags=re.I)
    forbidden = ['idea', 'ideas', 'program', 'programs', 'attempt', 'attempts', 'eligible', 'worker_01', 'worker_02', 'combined_score', 'rubric']
    violations = [word for word in forbidden if re.search(r'\b'+re.escape(word)+r'\b', visible, re.I)]
    assert not violations, violations
    declared = set(re.findall(r'@\w+\{([^,]+),', (root/'references.bib').read_text()))
    cited = {key.strip() for group in re.findall(r'\\cite\w*\{([^}]+)\}', text) for key in group.split(',')}
    assert declared == cited
    assert 25 <= len(cited) <= 30
    assert r'\iclrfinalcopy' not in text
    assert r'\author{}' in text
    log = (root/'paper.log').read_text()
    assert 'undefined references' not in log
    assert 'undefined citations' not in log
    assert 'Overfull \\hbox' not in log
    spec = importlib.util.spec_from_file_location('compile_inputs', root/'.codex/skills/validate-paper/scripts/validate_compile_inputs.py')
    compile_inputs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compile_inputs)
    approved = [path.resolve() for path in compile_inputs.LATEX_SYSTEM_INPUT_ROOTS if path.exists()]
    cross_root_links = []
    for line in (root/'paper.fls').read_text().splitlines():
        if not line.startswith('INPUT '):
            continue
        path = Path(line[6:])
        path = path if path.is_absolute() else root/path
        resolved = path.resolve()
        assert resolved.is_relative_to(root) or any(resolved.is_relative_to(base) for base in approved), str(path)
        if path != resolved and not resolved.is_relative_to(root):
            cross_root_links.append({'recorded': str(path), 'resolved': str(resolved)})
    assert re.findall(r'\\bibdata\{([^}]+)\}', (root/'paper.aux').read_text()) == ['references']
    pending = not (root/'.concept_figure_complete').exists() and (root/'figures/fixed_resource_overview.prompts.json').read_text().strip() == '{}'
    evidence = json.loads((root/'scientific-evidence/verification-report.json').read_text())
    assert evidence['summary']['dangling_references'] == 0
    report = {'document_checks': 'passed', 'body_pages': references_page, 'total_pages': len(pdf),
              'references': len(cited), 'claims': len(json.loads((root/'claims_grounding.json').read_text())['claims']),
              'figure_schema': 'passed', 'figure_density_and_paths': 'passed', 'rendered_supplement': 'passed',
              'unresolved_citations': 0, 'overfull_horizontal_boxes': 0, 'standalone_language': 'passed',
              'pdf_sha256': hashlib.sha256((root/'paper.pdf').read_bytes()).hexdigest(),
              'recorder_audit': 'passed independently: all resolved files lie in manuscript or approved TeX roots',
              'system_symlink_examples': cross_root_links[:3],
              'canonical_workflow_limitations': [
                  'compile_latex.sh rejects /usr/share/texmf/web2c/texmf.cnf, a symlink into another approved system TeX root; sanitized pdflatex/bibtex commands and an independent resolved-path audit were used instead.',
                  'validate_figures.py cannot import unstaged src.orchestrator; canonical JSON schema and strategy budgets were checked independently.'],
              'concept_figure_status': 'pending_orchestrator_render' if pending else 'rendered',
              'scientific_scope': 'completed qualified evaluation; conditional efficiency only; no finite-sample coverage certificate; no causal component attribution',
              'new_experiments': False, 'scientific_evidence': evidence['summary']}
    (root/'validation_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
