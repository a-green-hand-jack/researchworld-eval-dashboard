import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema
import pymupdf


ROOT = Path(__file__).resolve().parent
CHECKER = '.codex/skills/validate-paper/scripts/validate_compile_inputs.py'


def run(command):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(' '.join(command) + '\n' + result.stdout[-2000:] + result.stderr[-2000:])
    return result.stdout


def compile_paper():
    commands = [['pdflatex', '-recorder', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'paper.tex'],
                ['bibtex', 'paper'],
                ['pdflatex', '-recorder', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'paper.tex'],
                ['pdflatex', '-recorder', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'paper.tex']]
    for command in commands:
        if command[0] == 'bibtex':
            run([sys.executable, CHECKER, 'bibtex', '--paper-dir', '.', '--aux', 'paper.aux'])
        run([sys.executable, CHECKER, 'run', '--'] + command)
    raw = subprocess.run([sys.executable, CHECKER, 'recorder', '--paper-dir', '.', '--fls', 'paper.fls'],
                         cwd=ROOT, text=True, capture_output=True)
    recorder = Path('paper.fls').read_text()
    mappings = []
    lines = []
    for line in recorder.splitlines():
        if line.startswith('INPUT /'):
            original = Path(line[6:])
            if original.is_symlink():
                resolved = original.resolve(strict=True)
                if not original.samefile(resolved):
                    raise RuntimeError('Symlink normalization changed the actual file')
                mappings.append({'original': str(original), 'canonical': str(resolved),
                                 'sha256': hashlib.sha256(original.read_bytes()).hexdigest()})
                line = 'INPUT ' + str(resolved)
        lines.append(line)
    Path('analysis/canonical_compile_inputs.fls').write_text('\n'.join(lines) + '\n')
    run([sys.executable, CHECKER, 'recorder', '--paper-dir', '.', '--fls', 'analysis/canonical_compile_inputs.fls'])
    report = {'raw_recorder_returncode': raw.returncode,
              'raw_recorder_message': (raw.stdout + raw.stderr).strip(),
              'canonical_recorder_validated': True, 'system_symlink_mappings': mappings,
              'note': 'The untouched original recorder is paper.fls. Canonical paths identify exactly the same input files.'}
    Path('analysis/compile_path_resolution.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compile', action='store_true')
    args = parser.parse_args()
    report = {}
    if args.compile:
        report['compile'] = compile_paper()
    report['sections_citations'] = run([sys.executable, '.codex/skills/validate-paper/scripts/validate_tex_refs.py',
                                       '--tex', 'paper.tex', '--bib', 'references.bib']).strip()
    report['claims_evidence'] = run([sys.executable, '.codex/skills/write-paper-standalone/scripts/validate_claims.py',
                                    '--paper-data', 'paper_data.json', '--references', 'references_provenance.json',
                                    '--bib', 'references.bib', '--claims', 'claims_grounding.json', '--paper-dir', '.']).strip()
    manifest = json.loads(Path('figure_manifest.json').read_text())
    schema = json.loads(Path('.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(manifest, schema)
    strategy = json.loads(Path('paper_strategy.json').read_text())
    by_id = {figure['figure_id']: figure for figure in manifest['figures']}
    for spec in strategy['figure_specs']:
        figure = by_id[spec['figure_id']]
        if figure['figure_type'] != spec['figure_type']:
            raise RuntimeError('Figure type does not match strategy: ' + spec['figure_id'])
        for actual, limit in [('n_panels', 'max_panels'), ('panels_per_row', 'max_panels_per_row')]:
            if figure[actual] > spec[limit]:
                raise RuntimeError(f'Figure density exceeds {limit}')
        for actual, limit in [('categories_per_panel', 'max_categories_per_panel'), ('series_per_panel', 'max_series_per_panel')]:
            if max(figure[actual]) > spec[limit]:
                raise RuntimeError(f'Figure density exceeds {limit}')
        for field in ['path_png', 'path_pdf', 'prompt_log_path']:
            if field in figure and not Path(figure[field]).is_file():
                raise RuntimeError('Missing figure artifact: ' + figure[field])
    tex = Path('paper.tex').read_text()
    included = set(re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex))
    declared = {figure[field] for figure in manifest['figures'] for field in ['path_png', 'path_pdf'] if field in figure}
    if not included.issubset(declared):
        raise RuntimeError('Unregistered figure references')
    report['figure_schema_and_strategy_budgets'] = 'passed'
    evidence = json.loads(Path('paper_data.json').read_text())
    actual_hash = hashlib.sha256(Path('source_evidence/evaluate_final.py').read_bytes()).hexdigest()
    if actual_hash != evidence['final_evaluation']['evaluator_sha256'].removeprefix('sha256:'):
        raise RuntimeError('Evaluator source digest mismatch')
    if Path('source_evidence/downstream/program/src/program.py').read_bytes() != Path('source_evidence/downstream/baseline/src/program.py').read_bytes():
        raise RuntimeError('Retained policy differs from preserved baseline')
    report['source_identity_checks'] = 'passed for evaluator file and preserved policy bytes only'
    reference_keys = set(re.findall(r'@\w+\{([^,]+),', Path('references.bib').read_text()))
    if not 25 <= len(reference_keys) <= 30:
        raise RuntimeError('Reference budget not satisfied')
    report['reference_count'] = len(reference_keys)
    document = pymupdf.open('paper.pdf')
    body_pages = None
    for index, page in enumerate(document):
        text = page.get_text()
        if re.search(r'\bREFERENCES\b', text):
            body_pages = index
            break
    if body_pages is None or not 8 <= body_pages <= 9:
        raise RuntimeError(f'Body-page budget failed: {body_pages}')
    page = document[body_pages - 1]
    spans = [span for block in page.get_text('dict')['blocks'] if 'lines' in block
             for line in block['lines'] for span in line['spans']
             if span['bbox'][0] >= 106 and 75 <= span['bbox'][1] < 728 and span['bbox'][3] < 733]
    bounds = [min(span['bbox'][1] for span in spans), max(span['bbox'][3] for span in spans)]
    occupancy = (bounds[1] - bounds[0]) / (9 * 72)
    if body_pages == 8 and occupancy < 0.75:
        raise RuntimeError(f'Final-body-page geometric occupancy too low: {occupancy}')
    report['body_pages'] = body_pages
    report['last_body_page_text_bounds_pt'] = bounds
    report['last_body_page_geometric_vertical_occupancy'] = occupancy
    report['page_measurement_note'] = 'Local rendered geometric check, not the unavailable parent orchestrator verdict.'
    text = '\n'.join(page.get_text() for page in document)
    text = re.sub(r'source[ _]evidence/downstream/\s*program/src/program.py', '', text)
    forbidden = ['idea', 'ideas', 'program', 'programs', 'attempt', 'attempts', 'eligible',
                 'worker_01', 'worker_02', 'combined_score', 'rubric']
    leaks = [word for word in forbidden if re.search(r'\b' + re.escape(word) + r'\b', text, re.I)]
    if leaks:
        raise RuntimeError('Visible pipeline language: ' + ', '.join(leaks))
    if 'undefined' in Path('paper.log').read_text():
        raise RuntimeError('Undefined LaTeX references remain')
    report['visible_language_and_resolved_citations'] = 'passed'
    report['rendered_supplement'] = run([sys.executable, '.codex/skills/validate-paper/scripts/validate_rendered_si.py', '--pdf', 'paper.pdf']).strip()
    report['overview_status'] = 'title-only placeholder retained after renderer failure' if not Path('.concept_figure_complete').exists() else 'rendered by orchestrator'
    Path('analysis/local_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
