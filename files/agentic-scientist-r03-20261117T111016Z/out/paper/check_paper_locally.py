import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

import jsonschema
import pymupdf


def main():
    """@evidence[[paper.tex]]
    @evidence[[figure_manifest.json]]
    @evidence[[paper_data.json#/final_evaluation]]
    """
    report = dict(checks={}, canonical_limitations=[])
    manifest = json.loads(Path('figure_manifest.json').read_text())
    schema = json.loads(Path('.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(manifest, schema)
    report['checks']['figure_schema'] = True
    strategy = json.loads(Path('paper_strategy.json').read_text())
    specifications = {entry['figure_id']: entry for entry in strategy['figure_specs']}
    tex = Path('paper.tex').read_text()
    referenced = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex)
    for figure in manifest['figures']:
        spec = specifications[figure['figure_id']]
        assert figure['figure_type'] == spec['figure_type']
        assert figure['n_panels'] <= spec['max_panels']
        assert figure['panels_per_row'] <= spec['max_panels_per_row']
        assert max(figure['categories_per_panel']) <= spec['max_categories_per_panel']
        assert max(figure['series_per_panel']) <= spec['max_series_per_panel']
        for key in ['path_pdf', 'path_png', 'prompt_log_path']:
            if figure.get(key):
                assert Path(figure[key]).is_file()
        used = figure.get('path_pdf') or figure['path_png']
        assert used in referenced
        if figure['generator'] == 'matplotlib':
            assert figure['estimated_min_rendered_font_pt'] >= 8.5
    assert len(referenced) == len(manifest['figures'])
    report['checks']['figure_assets_and_strategy_budgets'] = True
    report['concept_render_status'] = 'rendered' if Path('.concept_figure_complete').exists() else 'placeholder; orchestrator rendering pending by contract'
    report['canonical_limitations'].append('Canonical validate_figures.py cannot import the unavailable src.orchestrator package; local JSON Schema, asset, density and placement checks are reported separately.')
    pdf = pymupdf.open('paper.pdf')
    page_texts = [page.get_text() for page in pdf]
    references = next(index for index, text in enumerate(page_texts) if re.search(r'(?m)^REFERENCES\s*$', text))
    assert 8 <= references <= 9
    blocks = [block for block in pdf[references - 1].get_text('blocks') if block[0] >= 100 and block[1] >= 75 and block[3] < 745]
    bottom = max(block[3] for block in blocks)
    occupancy = (bottom - 80) / 648
    assert references != 8 or occupancy >= .75
    report['checks']['body_pages'] = references
    report['checks']['last_body_page_geometric_vertical_fraction'] = occupancy
    report['checks']['total_pages'] = len(pdf)
    visible = '\n'.join(page_texts)
    forbidden = r'\b(?:idea|ideas|program|programs|attempt|attempts|eligible|worker_01|worker_02|combined_score|rubric)\b'
    assert not re.search(forbidden, visible, re.I)
    assert 'Anonymous authors' in visible
    assert not re.search(r'(?mi)^\s*(?:acknowledg\w*|funding)\s*$', visible)
    report['checks']['visible_language_and_anonymity'] = True
    si_path = Path('.codex/skills/validate-paper/scripts/validate_rendered_si.py')
    specification = importlib.util.spec_from_file_location('rendered_si', si_path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    assert not module.validate_rendered_supplementary_information(page_texts)
    report["checks"]["rendered_supplement_raw_pdf_text"] = True
    if shutil.which('pdftotext'):
        rendered = subprocess.run(['pdftotext', '-layout', 'paper.pdf', '-'], check=True, capture_output=True, text=True)
        rendered_pages = rendered.stdout.split('\f')
        report['rendered_supplement_extraction_backend'] = 'pdftotext'
    else:
        rendered_pages = []
        for page in pdf:
            rows = {}
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    if line['dir'] != (1.0, 0.0) or line['bbox'][0] < 100:
                        continue
                    text = ''.join(span['text'] for span in line['spans'])
                    rows.setdefault(round(line['bbox'][1], 1), []).append((line['bbox'][0], text))
            rendered_pages.append('\n'.join(' '.join(text for left, text in sorted(parts)) for top, parts in sorted(rows.items())))
        report['rendered_supplement_extraction_backend'] = 'PyMuPDF horizontal text rows, excluding margin line numbers and diagonal watermark'
        report['canonical_limitations'].append('Canonical compile workflow requires unavailable pdftotext; the rendered supplement is independently checked using PyMuPDF extraction.')
    assert not module.validate_rendered_supplementary_information(rendered_pages)
    report['checks']['rendered_supplement'] = True
    for stem in ['budget_details', 'seed_details']:
        assert Path('tables/' + stem + '.tex').read_text().strip() in tex
    report['checks']['embedded_supplement_tables_equal_generated_tables'] = True
    for target, pointer in re.findall(r'@evidence\[\[([^#\]]+)#(/[^\]]*)\]\]', tex):
        if target.endswith('.json'):
            value = json.loads(Path(target).read_text())
            for part in pointer[1:].split('/'):
                part = part.replace('~1', '/').replace('~0', '~')
                value = value[int(part)] if isinstance(value, list) else value[part]
    report['checks']['manuscript_json_pointers_resolve'] = True
    log = Path('paper.log').read_text()
    assert 'undefined' not in log.lower()
    assert 'Overfull' not in log
    report['checks']['no_unresolved_tex_references_or_overfull_boxes'] = True
    bibkeys = re.findall(r'@\w+\{([^,]+),', Path('references.bib').read_text())
    assert 25 <= len(bibkeys) <= 30
    report['checks']['reference_count'] = len(bibkeys)
    claims = json.loads(Path('claims_grounding.json').read_text())
    report['checks']['mapped_claims'] = len(claims['claims'])
    gate = subprocess.run(['python3', '.codex/skills/validate-paper/scripts/validate_compile_inputs.py', 'recorder', '--paper-dir', '.', '--fls', 'paper.fls'], capture_output=True, text=True)
    report['canonical_compile_input_gate'] = dict(passed=gate.returncode == 0, message=(gate.stdout + gate.stderr).strip())
    if gate.returncode:
        report['canonical_limitations'].append('Canonical recorder gate rejects Debian system texmf.cnf symlink. Direct compilation and independent resolved-path dependency checks succeeded; canonical gate is not reported as passed.')
        for line in Path('paper.fls').read_text().splitlines():
            if line.startswith('INPUT '):
                path = Path(line[6:]).resolve()
                assert path.is_relative_to(Path.cwd()) or any(path.is_relative_to(Path(root)) for root in ['/usr/share/texlive', '/etc/texmf', '/var/lib/texmf']), str(path)
    report['checks']['resolved_compilation_inputs_within_workspace_or_system_tex_roots'] = True
    Path('local_validation_report.json').write_text(json.dumps(report, indent=2))
    for index in [0, 1, references - 1, references + 2]:
        pdf[index].get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3)).save('/tmp/manuscript_page_' + str(index + 1) + '.png')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
