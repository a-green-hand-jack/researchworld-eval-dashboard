import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import jsonschema
import numpy as np
import pymupdf


def main():
    started = time.monotonic()
    data = json.loads(Path('paper_data.json').read_text())
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    episodes = data['final_evaluation']['evaluation_evidence']['episodes']
    summary = json.loads(Path('analysis_summary.json').read_text())
    reconstructed = {method: np.mean([case['curves'][method]
                        for episode in episodes for case in episode['solution']['cases']
                        if not case['permuted']]) for method in ['candidate', 'disagreement', 'random']}
    metrics = data['final_evaluation']['metrics']
    for method, key in [('candidate', 'combined_score'), ('disagreement', 'disagreement_baseline_score'),
                        ('random', 'random_baseline_score')]:
        assert np.isclose(reconstructed[method], metrics[key], rtol=0, atol=1e-15)
    assert data['grounding_sources']['final.qualification.outcome']['value'] == data['final_evaluation']['outcome']
    assert data['grounding_sources']['final.qualification.status']['value'] == data['final_evaluation']['status']

    manifest = json.loads(Path('figure_manifest.json').read_text())
    schema = json.loads(Path('.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
    jsonschema.validate(manifest, schema)
    specs = {entry['figure_id']: entry for entry in json.loads(Path('paper_strategy.json').read_text())['figure_specs']}
    for entry in manifest['figures']:
        spec = specs[entry['figure_id']]
        assert entry['panel_count'] <= spec['max_panels']
        assert entry['panels_per_row'] <= spec['max_panels_per_row']
        assert entry['estimated_min_rendered_font_pt'] >= spec['min_rendered_font_pt']
        assert all(Path(path).is_file() for path in entry['files'].values())
        assert all(source in data['grounding_sources'] for source in entry['source_ids'])
        for panel in entry['panels']:
            assert panel['category_count'] <= spec['max_categories_per_panel']
            assert panel['series_count'] <= spec['max_series_per_panel']
    text = Path('paper.tex').read_text()
    for token in re.findall(r'@evidence\[\[([^]]+)\]\]', text):
        target, separator, locator = token.partition('#')
        assert Path(target).is_file()
        if separator and locator.startswith('/'):
            value = json.loads(Path(target).read_text())
            for segment in locator.lstrip('/').split('/'):
                segment = segment.replace('~1', '/').replace('~0', '~')
                value = value[int(segment)] if isinstance(value, list) else value[segment]
        elif separator and re.fullmatch(r'L\d+', locator):
            assert int(locator[1:]) <= len(Path(target).read_text().splitlines())
    referenced = re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', text)
    declared = {path for entry in manifest['figures'] for path in entry['files'].values()}
    assert set(referenced) <= declared
    bibliography = set(re.findall(r'@\w+\{([^,]+),', Path('references.bib').read_text()))
    assert 25 <= len(bibliography) <= 30

    document = pymupdf.open('paper.pdf')
    page_texts = [page.get_text() for page in document]
    references_page = next(index for index, contents in enumerate(page_texts)
                           if re.search(r'(?m)^R\s*E\s*F\s*E\s*R\s*E\s*N\s*C\s*E\s*S\s*$', contents))
    assert 8 <= references_page <= 9
    supplement_page = next(index for index, contents in enumerate(page_texts)
                            if re.search(r'S\s*U\s*P\s*P\s*L\s*E\s*M\s*E\s*N\s*T\s*A\s*R\s*Y\s+I\s*N\s*F\s*O\s*R\s*M\s*A\s*T\s*I\s*O\s*N', contents))
    assert supplement_page > references_page
    last_body_page = document[references_page - 1]
    spans = [span for block in last_body_page.get_text('dict')['blocks'] if 'lines' in block
             for line in block['lines'] for span in line['spans']]
    content = [span for span in spans if 8 <= span['size'] <= 15 and span['bbox'][0] >= 105
               and span['bbox'][2] <= 509 and 75 <= span['bbox'][1] <= 735
               and not span['text'].strip().isdigit()]
    content_bottom = max(span['bbox'][3] for span in content)
    body_top, body_height = 84, 648
    estimated_fill = (content_bottom - body_top) / body_height
    if references_page == 8:
        assert estimated_fill >= 0.75
    visible = '\n'.join(page_texts)
    banned = re.findall(r'\b(?:idea|ideas|program|programs|attempt|attempts|eligible|worker_01|worker_02|combined_score|rubric)\b', visible, re.I)
    assert not banned, banned
    assert 'LLM USAGE' in visible.upper() or 'L L M U S A G E' in visible.upper()
    report = {'status': 'local_artifact_checks_passed',
              'paper_data_sha256': hashlib.sha256(Path('paper_data.json').read_bytes()).hexdigest(),
              'qualification': {key: data['grounding_sources']['final.qualification.' + key]['value']
                                for key in ['status', 'outcome', 'correct']},
              'aggregate_reconstruction': {key: float(value) for key, value in reconstructed.items()},
              'claim_count': len(json.loads(Path('claims_grounding.json').read_text())['claims']),
              'reference_count': len(bibliography), 'pdf_pages': len(document),
              'body_pages': references_page, 'references_start_page': references_page + 1,
              'supplement_start_page': supplement_page + 1,
              'last_body_geometric_fill_estimate': estimated_fill,
              'geometry_note': 'PyMuPDF body-text bounds, excluding watermark, line numbers and footer. Parent venue validator remains authoritative.',
              'canonical_figure_schema': 'passed', 'strategy_density_and_paths': 'passed',
              'manuscript_json_pointers_and_line_locators': 'passed',
              'visible_language_scan': 'passed',
              'concept_figure': 'completed' if Path('.concept_figure_complete').exists() else 'guarded placeholder; synchronous parent render pending',
              'integrated_figure_validator': 'unavailable: launcher requires unstaged src.orchestrator module',
              'raw_to_partition_reproduction': 'incomplete; missing original builder and archives disclosed',
              'local_check_elapsed_seconds': time.monotonic() - started}
    Path('paper_validation_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
