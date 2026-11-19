import json
import re
from pathlib import Path

import jsonschema
import numpy as np
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parent


def main():
    manifest = json.loads((ROOT / 'figure_manifest.json').read_text())
    schema = json.loads((ROOT / '.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(manifest, schema)
    specs = {spec['figure_id']: spec for spec in json.loads((ROOT / 'paper_strategy.json').read_text())['figure_specs']}
    for figure in manifest['figures']:
        assert figure['figure_type'] == specs[figure['figure_id']]['figure_type']
        if figure['generator'] == 'matplotlib':
            with Image.open(ROOT / figure['files']['png']) as image:
                assert image.width >= 2400
                assert np.allclose(image.info['dpi'], [300, 300], atol=.01)
    verified_pointers = 0
    for path in [ROOT / 'paper.tex', ROOT / 'claims_grounding.json', ROOT / 'build_paper_artifacts.py']:
        for target, pointer in re.findall(r'@evidence\[\[([^#\]]+)#(/[^\]]*)\]\]', path.read_text()):
            value = json.loads((ROOT / target).read_text())
            for part in pointer.lstrip('/').split('/'):
                part = part.replace('~1', '/').replace('~0', '~')
                value = value[int(part)] if isinstance(value, list) else value[part]
            verified_pointers += 1
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    data = json.loads((ROOT / 'paper_data.json').read_text())
    summary = json.loads((ROOT / 'derived_results.json').read_text())
    assert sum(map(len, summary['common_support'].values())) == 28
    assert summary['common_support']['commonsense'] == [7001]
    assert data['final_evaluation']['outcome'] == 'not_qualified'
    for episode in data['final_evaluation']['evaluation_evidence']['episodes']:
        for name, case in episode['solution']['cases'].items():
            if episode['seed'] in summary['common_support'][name]:
                truth = np.asarray(case['target_full_means'])
                array = np.asarray(case['conditions']['primary']['predictions'])
                expected = summary['case_seed_mae'][summary['cases'].index(name)][summary['seeds'].index(episode['seed'])][0]
                assert np.isclose(np.abs(array - truth).mean(), expected, rtol=1e-12, atol=1e-12)
    tex = (ROOT / 'paper.tex').read_text()
    referenced = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex)
    assert set(referenced) == {figure['files'].get('pdf', figure['files']['png']) for figure in manifest['figures']}
    for figure in manifest['figures']:
        for path in figure['files'].values():
            assert (ROOT / path).is_file()
        assert figure['estimated_min_rendered_font_pt'] >= 8.5
    document = pymupdf.open(ROOT / 'paper.pdf')
    text_pages = [page.get_text() for page in document]
    references_page = next(index for index, text in enumerate(text_pages) if re.search(r'\bREFERENCES\b', text))
    supplement_page = next(index for index, text in enumerate(text_pages) if re.search(r'SUPPLEMENTARY\s+INFORMATION', text))
    assert references_page in [8, 9], references_page
    assert supplement_page > references_page
    last_body = document[references_page - 1]
    blocks = [block for block in last_body.get_text('blocks') if block[0] > 100 and block[1] > 60 and block[3] < 730]
    body_bottom = max(block[3] for block in blocks)
    fill = (body_bottom - 72) / (9 * 72)
    assert references_page == 9 or fill >= .75
    body_text = '\n'.join(text_pages[:references_page])
    forbidden = ['idea', 'ideas', 'program', 'programs', 'attempt', 'attempts', 'eligible', 'worker_01', 'worker_02', 'combined_score', 'rubric']
    assert not re.search(r'\b(?:' + '|'.join(forbidden) + r')\b', body_text, re.I)
    assert 'failed qualification' in body_text.lower() or 'failed\nqualification' in body_text.lower()
    approved_roots = [ROOT] + [Path(root).resolve() for root in ['/etc/texmf', '/opt/texlive', '/usr/share/texlive', '/usr/share/texmf', '/var/lib/texmf']]
    recorder_inputs = set()
    for line in (ROOT / 'paper.fls').read_text().splitlines():
        if line.startswith('INPUT '):
            path = Path(line[6:])
            resolved = (path if path.is_absolute() else ROOT / path).resolve()
            assert any(resolved.is_relative_to(root) for root in approved_roots), str(resolved)
            recorder_inputs.add(str(resolved))
    report = dict(figure_schema='passed', figure_strategy_types='passed', quantitative_png_resolution='passed', json_pointers_checked=verified_pointers,
                  available_pair_recalculation='passed', figures_referenced='passed',
                  body_pages=references_page, last_body_geometric_fill=fill,
                  supplementary_start_page=supplement_page + 1, standalone_language='passed',
                  resolved_recorder_inputs_checked=len(recorder_inputs),
                  note='Local checks supplement separately run canonical figure validation. Orchestrator-owned diagram remains a documented failed-render placeholder. Canonical full compilation still requires pdftotext and portable TeX recorder-root handling.')
    (ROOT / 'local_validation_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
