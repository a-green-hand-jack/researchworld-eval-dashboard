import datetime
import hashlib
import json
import re
from pathlib import Path

import jsonschema
import numpy as np
import pymupdf
from PIL import Image


ROOT = Path(__file__).resolve().parent


def main():
    # @evidence[[paper_data.json#final_evaluation]]
    # @evidence[[source_evidence/evaluation/plan.json]]
    # @evidence[[iclr2026_conference.sty]]
    payload = json.loads((ROOT / 'paper_data.json').read_text())
    final = payload['final_evaluation']
    metrics = final['metrics']
    episodes = final['evaluation_evidence']['episodes']
    actual = [item for episode in episodes for item in episode['solution']['cases']
              if not item['control'] and not item['replay']]
    controls = [item for episode in episodes for item in episode['solution']['cases']
                if item['control'] and not item['replay']]
    errors = []

    def require(condition, description):
        if not condition:
            errors.append(description)

    require(np.isclose(np.mean([item['score'] for item in actual]), metrics['combined_score']), 'Primary pooled score mismatch')
    require(np.isclose(np.mean([item['score'] for item in controls]), metrics['permuted_score']), 'Control pooled score mismatch')
    require(np.isclose(metrics['combined_score'] - metrics['permuted_score'], metrics['corruption_gap']), 'Corruption gap mismatch')
    for method in ['constant', 'copy', 'random_lowrank', 'medoid_ridge', 'selected_ridge']:
        require(np.isclose(np.mean([item['baselines'][method] for item in actual]), metrics[method + '_score']), method + ' pooled score mismatch')
    for source in ['mteb', 'open_llm']:
        require(np.isclose(np.mean([item['score'] for item in actual if item['source'] == source]), metrics[source + '_score']), source + ' pooled score mismatch')
    require(all(np.isclose(np.mean(item['curve']), item['score']) for item in actual + controls), 'Recorded checkpoint/case means disagree')

    manifest = json.loads((ROOT / 'figure_manifest.json').read_text())
    schema = json.loads((ROOT / '.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(manifest, schema)
    strategy = json.loads((ROOT / 'paper_strategy.json').read_text())
    specs = {item['figure_id']: item for item in strategy['figure_specs']}
    figures = {item['figure_id']: item for item in manifest['figures']}
    for name, specification in specs.items():
        require(name in figures, 'Missing planned figure: ' + name)
        figure = figures[name]
        require(figure['panel_count'] <= specification['max_panels'], name + ' exceeds panel budget')
        require(figure['panels_per_row'] <= specification['max_panels_per_row'], name + ' exceeds row budget')
        for panel in figure['panels']:
            require(panel['category_count'] <= specification['max_categories_per_panel'], name + ' exceeds category budget')
            require(panel['series_count'] <= specification['max_series_per_panel'], name + ' exceeds series budget')
    tex = (ROOT / 'paper.tex').read_text()
    graphics = re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', tex)
    for graphic in graphics:
        require((ROOT / graphic).is_file(), 'Missing referenced figure: ' + graphic)
        require(any(graphic in entry['files'].values() for entry in figures.values()), 'Unregistered figure: ' + graphic)
    for name, entry in figures.items():
        for path in entry['files'].values():
            require((ROOT / path).is_file(), 'Missing manifest artifact: ' + path)
        if entry['generator'] == 'matplotlib':
            with Image.open(ROOT / entry['files']['png']) as image:
                require(abs(image.info.get('dpi', (0, 0))[0] - 300) < 1, name + ' PNG is not 300 DPI')
            require(entry['estimated_min_rendered_font_pt'] >= 8.5, name + ' estimated font too small')

    document = pymupdf.open(ROOT / 'paper.pdf')
    texts = [page.get_text() for page in document]
    reference_index = next(index for index, text in enumerate(texts) if re.search(r'(?m)^REFERENCES\s*$', text))
    supplementary_index = next(index for index, text in enumerate(texts) if 'SUPPLEMENTARY INFORMATION' in text)
    require(supplementary_index > reference_index, 'Rendered supplementary section not after references')
    body_page_count = reference_index
    require(8 <= body_page_count <= 9, 'Body page count outside venue budget')
    last_page = document[reference_index - 1]
    positions = []
    for block in last_page.get_text('dict')['blocks']:
        if block['type'] != 0:
            continue
        for line in block['lines']:
            for span in line['spans']:
                horizontal, vertical, right, bottom = span['bbox']
                if 105 <= horizontal < 510 and 80 <= vertical < 732 and not re.fullmatch(r'\d+', span['text'].strip()):
                    positions.append(bottom)
    last_body_extent = (max(positions) - 84) / (9 * 72)
    if body_page_count == 8:
        require(last_body_extent >= .75, 'Last body page geometric extent below 75 percent')
    require('Anonymous authors' in texts[0], 'Anonymous review block not rendered')
    template_record = json.loads((ROOT / 'template_provenance.json').read_text())
    require(hashlib.sha256((ROOT / 'iclr2026_conference.sty').read_bytes()).hexdigest() == template_record['sha256'], 'Official template content hash mismatch')
    log = (ROOT / 'paper.log').read_text()
    require('Overfull \\hbox' not in log, 'LaTeX contains an overfull horizontal box')
    require('undefined references' not in log and 'Citation `' not in log, 'LaTeX references unresolved')

    visible = re.sub(r'%[^\n]*', '', tex)
    visible = re.sub(r'\\(?:path|texttt|url)\{[^}]*\}', '', visible)
    visible = re.sub(r'\\begin\{verbatim\}.*?\\end\{verbatim\}', '', visible, flags=re.DOTALL)
    require(not re.search(r'\b(?:idea|ideas|program|programs|attempt|attempts|eligible|worker_01|worker_02|combined_score|rubric)\b', visible, re.I), 'Private pipeline language outside literal paths')

    source = ROOT / 'source_evidence/downstream/program/src/program.py'
    baseline = ROOT / 'source_evidence/downstream/baseline/src/program.py'
    require(source.read_bytes() == baseline.read_bytes(), 'Readable retained/reference sources differ')
    evidence_report = json.loads((ROOT / 'scientific-evidence/verification-report.json').read_text())
    summary = evidence_report.get('summary', {})
    require(summary.get('dangling_references', 0) == 0, 'Evidence report has dangling references')

    allowed_roots = [Path(path).resolve() for path in ['/etc/texmf', '/usr/share/texlive', '/usr/share/texmf', '/usr/share/texmf-dist', '/var/lib/texmf', '/usr/local/share/texmf']]
    realpath_audit_failures = []
    for line in (ROOT / 'paper.fls').read_text().splitlines():
        if not line.startswith('INPUT '):
            continue
        path = Path(line[6:])
        resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
        if not resolved.is_relative_to(ROOT) and not any(resolved.is_relative_to(root) for root in allowed_roots):
            realpath_audit_failures.append(str(resolved))
    require(not realpath_audit_failures, 'Non-workspace/non-system resolved TeX input')

    report = {'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Local manuscript/artifact checks; not a replacement for parent orchestration validation',
        'local_hard_errors': errors, 'body_pages': body_page_count,
        'last_body_page_geometric_extent_fraction': last_body_extent,
        'pdf_pages': len(document), 'active_references': len(json.loads((ROOT / 'references_provenance.json').read_text())['references']),
        'mapped_claims': len(json.loads((ROOT / 'claims_grounding.json').read_text())['claims']),
        'scientific_evidence_summary': summary, 'figure_manifest_schema': 'passed',
        'planned_figure_density': 'passed', 'numerical_summary_consistency': 'passed' if not errors else 'see errors',
        'realpath_tex_dependency_audit': 'passed' if not realpath_audit_failures else realpath_audit_failures,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'sealed_source_identity': 'not independently certified; qualification/results read separately',
        'canonical_environment_limitations': [
            'validate_figures.py cannot import absent src.orchestrator module; canonical schema/density/file/font checks performed locally.',
            'compile_latex.sh recorder validation rejects /usr/share/texmf/web2c/texmf.cnf, a distribution symlink to another approved system root. Unmodified canonical sanitized runner used for pdflatex/BibTeX, and all actual resolved dependencies independently audited.'
        ],
        'orchestrator_pending': ['Replace guarded conceptual overview placeholder and prompt-log stub, then recompile; no quantitative figure is pending.']}
    (ROOT / 'validation_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
