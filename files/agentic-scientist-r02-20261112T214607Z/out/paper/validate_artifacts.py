import hashlib
import json
import re
from pathlib import Path

import jsonschema
import pymupdf
from PIL import Image


data = json.loads(Path('paper_data.json').read_text())
summary = json.loads(Path('analysis_summary.json').read_text())
manifest = json.loads(Path('figure_manifest.json').read_text())
schema = json.loads(Path('.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
jsonschema.validate(manifest, schema)
strategies = {entry['figure_id']: entry for entry in json.loads(Path('paper_strategy.json').read_text())['figure_specs']}
for figure in manifest['figures']:
    plan = strategies[figure['figure_id']]
    assert figure['n_panels'] <= plan['max_panels']
    assert figure['panels_per_row'] <= plan['max_panels_per_row']
    assert max(figure['categories_per_panel']) <= plan['max_categories_per_panel']
    assert max(figure['series_per_panel']) <= plan['max_series_per_panel']
    assert figure['estimated_min_rendered_font_pt'] >= 8
    assert Path(figure['path_png']).exists()
    if figure.get('path_pdf'):
        assert Path(figure['path_pdf']).exists()
        assert Image.open(figure['path_png']).info['dpi'][0] >= 299
    else:
        assert Image.open(figure['path_png']).width >= 2400

document = pymupdf.open('paper.pdf')
pages = [page.get_text() for page in document]
reference_index = next(index for index, text in enumerate(pages) if re.search(r'\bREFERENCES\b', text))
assert 8 <= reference_index <= 9
assert any('SUPPLEMENTARY INFORMATION' in text for text in pages[reference_index + 1:])
assert any('LLM USAGE' in text for text in pages)
visible = '\n'.join(pages)
for forbidden in ['eligible', 'combined_score', 'rubric', 'worker_01', 'worker_02', 'attempts', 'ideas', 'programs']:
    assert not re.search(r'\b' + re.escape(forbidden) + r'\b', visible, re.I), forbidden
assert len(json.loads(Path('references_provenance.json').read_text())['references']) == 25
assert abs(summary['aggregate']['actual']['utility'] - data['final_evaluation']['metrics']['combined_score']) < 1e-12
# @evidence[[paper_data.json#/final_evaluation/metrics]]
# @evidence[[analysis_summary.json#/aggregate]]
manuscript = Path('paper.tex').read_text()
for table in ['condition_utility', 'group_mass']:
    assert Path('tables', table + '.tex').read_text().strip() in manuscript

page = document[reference_index - 1]
words = [word for word in page.get_text('words') if word[0] >= 107 and word[2] <= 505 and word[1] < 738]
vertical_span = max(word[3] for word in words) - min(word[1] for word in words)
assert vertical_span / (9 * 72) >= .75
source_hash = hashlib.sha256(Path('source_evidence/evaluate_final.py').read_bytes()).hexdigest()
assert 'sha256:' + source_hash == data['final_evaluation']['evaluator_sha256']
report = dict(status='passed_local_checks', body_pages=reference_index,
              total_pdf_pages=len(document), reference_count=25,
              final_body_page_text_extent_fraction=vertical_span / (9 * 72),
              final_qualification={key: data['grounding_sources']['final.qualification.' + key]['value']
                                   for key in ['status', 'outcome', 'correct']},
              checks=['Canonical figure JSON schema', 'Strategy panel and density limits',
                      'Raster resolution and vector artifacts', 'Rendered sections and language',
                      'Aggregate value agreement', 'Exact supplementary table agreement',
                      'Copied evaluator hash matches frozen evaluator identifier'],
              limitations=['This script is not the parent orchestrator venue/page validator.',
                           'The canonical figure-validation entrypoint cannot import its unavailable src package here; schema and density checks are local.',
                           'The conceptual overview is an orchestrator-owned placeholder pending the synchronous render step.',
                           'No independent exact selected-source-tree identity proof or new scientific evaluation was performed.'])
Path('local_validation_report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
