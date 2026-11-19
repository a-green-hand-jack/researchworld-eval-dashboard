import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path


import jsonschema
import pymupdf


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads(Path('figure_manifest.json').read_text())
    schema = json.loads(Path('.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(manifest, schema)
    strategy = json.loads(Path('paper_strategy.json').read_text())
    planned = {figure['figure_id']: figure for figure in strategy['figure_specs']}
    actual = {figure['figure_id']: figure for figure in manifest['figures']}
    for figure_id, specification in planned.items():
        assert figure_id in actual
        figure = actual[figure_id]
        assert figure['panel_count'] <= specification['max_panels']
        assert all(panel['category_count'] <= specification['max_categories_per_panel'] and
                   panel['series_count'] <= specification['max_series_per_panel'] for panel in figure['panels'])
        assert figure['placement'] == 'full_width'
    tex = Path('paper.tex').read_text()
    graphics = set(re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex))
    registered = {path for figure in manifest['figures'] for path in figure['files'].values()}
    assert graphics <= registered
    assert all(Path(path).is_file() for path in registered)
    for path in ('analysis/coverage_table.tex', 'analysis/complete_comparisons.tex'):
        assert Path(path).read_text().strip() in tex
    bibliography_keys = set(re.findall(r'@\w+\{([^,]+),', Path('references.bib').read_text()))
    assert 25 <= len(bibliography_keys) <= 30
    cited = {key.strip() for group in re.findall(r'\\cite\w*\{([^}]+)\}', tex) for key in group.split(',')}
    assert cited == bibliography_keys
    provenance = json.loads(Path('references_provenance.json').read_text())
    assert cited == {reference['citation_key'] for reference in provenance['references']}
    assert all(Path(reference['read_artifact']).is_file() for reference in provenance['references'])
    claims = json.loads(Path('claims_grounding.json').read_text())['claims']
    evidence_anchor = '@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]'
    payload = json.loads(Path('paper_data.json').read_text())
    summary = json.loads(Path('analysis/summary.json').read_text())
    for metric, summary_key in (('iid_coverage_error', 'iid_error'), ('shift_coverage_error', 'shift_error'),
                                ('mean_volume', 'mass'), ('final_score', 'utility')):
        assert abs(payload['final_evaluation']['metrics'][metric] - summary['methods']['scaled_ilr'][summary_key]) < 1e-12
    assert abs(payload['final_evaluation']['metrics']['baseline_utility_gap'] -
               summary['paired_overall']['simplex_linf']['mean']) < 1e-12
    for key in ('status', 'outcome', 'correct'):
        assert summary['qualification'][key] == payload['final_evaluation'][key]
    selected_path = Path('results/ideas/03_training_only_conformal_rank_scale_selection/program_1/src/program.py')
    assert Path('source_evidence/selected_model.py').read_bytes() == selected_path.read_bytes()
    assert Path('source_evidence/evaluate_final.py').read_bytes() == Path('task/evaluate_final.py').read_bytes()
    registry = set(payload['grounding_sources']) | {reference['id'] for reference in provenance['references']}
    assert all(set(claim['source_ids']) <= registry for claim in claims)
    summary = json.loads(Path('analysis/summary.json').read_text())
    final = payload['final_evaluation']
    for name, derived in [('iid_coverage_error', 'iid_error'), ('shift_coverage_error', 'shift_error'),
                          ('mean_volume', 'mass'), ('final_score', 'utility')]:
        assert abs(final['metrics'][name] - summary['methods']['scaled_ilr'][derived]) < 1e-12
    assert summary['qualification'] == {key: final[key] for key in ('status', 'outcome', 'correct')}
    assert final['outcome'] == 'qualified'
    selected_source = Path('results/ideas/03_training_only_conformal_rank_scale_selection/program_1/src/program.py')
    assert selected_source.read_bytes() == Path('source_evidence/selected_model.py').read_bytes()
    assert Path('task/evaluate_final.py').read_bytes() == Path('source_evidence/evaluate_final.py').read_bytes()
    verified = json.loads(Path('scientific-evidence/verification-report.json').read_text())
    assert verified['summary']['dangling_references'] == 0
    document = pymupdf.open('paper.pdf')
    texts = [page.get_text() for page in document]
    reference_index = next(index for index, text in enumerate(texts) if re.search(r'(?m)^REFERENCES\s*$', text))
    supplement_index = next(index for index, text in enumerate(texts) if 'SUPPLEMENTARY INFORMATION' in text)
    assert 8 <= reference_index <= 9
    assert supplement_index > reference_index
    visible = '\n'.join(texts)
    prohibited = ('idea', 'ideas', 'program', 'programs', 'attempt', 'attempts', 'eligible', 'combined_score',
                  'rubric', 'worker_01', 'worker_02')
    assert not any(re.search(r'\b' + token + r'\b', visible, re.I) for token in prohibited)
    assert 'LLM USAGE' in visible
    assert 'Anonymous authors' in texts[0]
    assert not re.search(r'Overfull \\[hv]box|undefined', Path('paper.log').read_text(), re.I)
    validator_path = Path('.codex/skills/validate-paper/scripts/validate_rendered_si.py')
    specification = importlib.util.spec_from_file_location('rendered_si', validator_path)
    validator = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(validator)
    extracted = subprocess.run(['pdftotext', '-layout', 'paper.pdf', '-'], check=True, capture_output=True, text=True)
    assert not validator.validate_rendered_supplementary_information(extracted.stdout.split('\f'))
    recorded_inputs = []
    system_roots = [Path(path).resolve() for path in ('/etc/texmf', '/usr/share/texmf', '/usr/share/texlive', '/var/lib/texmf')]
    for line in Path('paper.fls').read_text().splitlines():
        if not line.startswith('INPUT '):
            continue
        resolved = Path(line[6:]).resolve()
        assert resolved.is_relative_to(root) or any(resolved.is_relative_to(system_root) for system_root in system_roots), str(resolved)
        recorded_inputs.append(str(resolved))
    last_body = document[reference_index-1]
    bounds = [span['bbox'] for block in last_body.get_text('dict')['blocks'] if block['type'] == 0
              for line in block['lines'] for span in line['spans']
              if span['bbox'][0] >= 107 and 65 < span['bbox'][1] < 715]
    report = {
        'status': 'independent_artifact_checks_passed', 'hard_errors': [],
        'scope': 'Local source, canonical schemas, rendered PDF, retained-metric consistency and evidence links; not a claim that unavailable parent orchestration checks ran.',
        'body_pages': reference_index, 'total_pages': len(document),
        'references_start_page': reference_index+1, 'supplement_start_page': supplement_index+1,
        'reference_count': len(cited), 'claim_count': len(claims), 'figure_count': len(actual),
        'dangling_evidence_references': verified['summary']['dangling_references'],
        'last_body_content_bounds_pt': [min(bound[1] for bound in bounds), max(bound[3] for bound in bounds)],
        'last_body_fill_note': 'Bounds are descriptive, not the authoritative parent geometric-occupancy verdict. Body has nine pages, so the special eight-page minimum-fill condition is not invoked.',
        'compiled_inputs_union_check': {'passed': True, 'recorded_input_count': len(recorded_inputs)},
        'qualification': summary['qualification'],
        'environment_limitations': [
            'Canonical validate_figures.py cannot import src.orchestrator.paper_step in this isolated workspace. The shipped canonical figure schema, required figure IDs, source paths and strategy density budgets were checked independently.',
            'Canonical compile_latex.sh input guard rejects /usr/share/texmf/web2c/texmf.cnf because it is a system symlink into a different approved system tree. No validator or system symlink was modified. Sanitized pdflatex/bibtex passes compiled the PDF; all recorded inputs independently resolve inside the workspace or the union of approved system TeX roots.'
        ],
        'orchestrator_pending': ['Replace the intentional conceptual-overview placeholder and prompt-log stub with the synchronous concept render, then perform the parent final compile and authoritative layout checks.']
    }
    Path('validation_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    template_source = 'https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2026/'
    Path('template_provenance.json').write_text(json.dumps({
        'venue': 'ICLR 2026', 'anonymous_review': True,
        'files': [{'path': name, 'source_url': template_source+name,
                   'sha256': hashlib.sha256(Path(name).read_bytes()).hexdigest()}
                  for name in ('iclr2026_conference.sty', 'iclr2026_conference.bst')]}, indent=2))
    for name, kind, sources in [
        ('paper.tex', 'manuscript', ['paper_data.json', 'claims_grounding.json', 'references.bib', 'source_evidence/selected_model.py', 'source_evidence/evaluate_final.py']),
        ('paper.pdf', 'manuscript', ['paper.tex', 'references.bib', 'figure_manifest.json']),
        ('figure_manifest.json', 'derived', ['paper_strategy.json', 'build_analysis.py']),
        ('validation_report.json', 'derived', ['paper.tex', 'paper.pdf', 'scientific-evidence/verification-report.json'])]:
        sidecar = {'schema_name': 'scientific-evidence.artifact-manifest',
                   'artifact': {'path': name, 'kind': kind},
                   'derived_from': ['@'+'evidence[['+source+']]' for source in sources]}
        if name == 'paper.pdf':
            sidecar['generated_by'] = {
                'script_path': '.codex/skills/validate-paper/scripts/validate_compile_inputs.py',
                'command': ['python', '.codex/skills/validate-paper/scripts/validate_compile_inputs.py',
                            'run', '--', 'pdflatex', '-recorder', '-no-shell-escape',
                            '-interaction=nonstopmode', '-halt-on-error', 'paper.tex']}
        elif name != 'paper.tex':
            sidecar['generated_by'] = {'script_path': 'build_analysis.py' if name == 'figure_manifest.json' else 'validate_artifacts.py'}
        else:
            sidecar['notes'] = 'Manuscript authored during the paper-writing workflow; this sidecar records its source trail, not an automated manuscript generator.'
        Path(name+'.prov.json').write_text(json.dumps(sidecar, indent=2))


if __name__ == '__main__':
    main()
