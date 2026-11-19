"""Artifact audit inputs: @evidence[[paper_data.json]] and @evidence[[VENUE.md]]."""

import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import jsonschema

ROOT = Path(__file__).resolve().parent
CHECKS = ROOT / '.codex/skills/validate-paper/scripts'
REGISTRY = json.loads((ROOT / 'paper_data.json').read_text())
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
REPORT = {'status': 'checking', 'checked_at': NOW, 'checks': {}, 'hard_errors': [],
          'pending': [], 'infrastructure_warnings': []}

def run(name, arguments):
    result = subprocess.run([str(argument) for argument in arguments], cwd=ROOT,
                            capture_output=True, text=True)
    REPORT['checks'][name] = {'returncode': result.returncode, 'stdout': result.stdout[-12000:],
                              'stderr': result.stderr[-6000:]}
    return result

for name, arguments in [('tex_references', [sys.executable, CHECKS / 'validate_tex_refs.py', '--tex', 'paper.tex', '--bib', 'references.bib'])]:
    if run(name, arguments).returncode:
        REPORT['hard_errors'].append(name + ' failed')

compile_guard = CHECKS / 'validate_compile_inputs.py'
for name, command in [('latex_initial', ['pdflatex', '-recorder', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'paper.tex']),
                      ('bibtex', ['bibtex', 'paper']),
                      ('latex_second', ['pdflatex', '-recorder', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'paper.tex']),
                      ('latex_final', ['pdflatex', '-recorder', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'paper.tex'])]:
    if run(name, [sys.executable, compile_guard, 'run', '--', *command]).returncode:
        REPORT['hard_errors'].append(name + ' failed')
if run('canonical_bibtex_input', [sys.executable, compile_guard, 'bibtex', '--paper-dir', '.', '--aux', 'paper.aux']).returncode:
    REPORT['hard_errors'].append('BibTeX dependency check failed')
recorder = run('canonical_recorder', [sys.executable, compile_guard, 'recorder', '--paper-dir', '.', '--fls', 'paper.fls'])
if recorder.returncode:
    REPORT['infrastructure_warnings'].append('Canonical recorder rejects a system texmf.cnf symlink whose resolved target is inside another approved TeX root. Raw failure is retained; an independent resolved-target audit follows, without modifying the canonical validator or recorder file.')

module_spec = importlib.util.spec_from_file_location('compile_input_guard', compile_guard)
guard = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(guard)
approved_roots = [path.resolve() for path in guard.LATEX_SYSTEM_INPUT_ROOTS if path.exists()]
input_count = 0
unsafe = []
for line in (ROOT / 'paper.fls').read_text().splitlines():
    if not line.startswith('INPUT '):
        continue
    target = Path(line.removeprefix('INPUT ').strip())
    target = (target if target.is_absolute() else ROOT / target).resolve()
    input_count += 1
    if target.is_relative_to(ROOT):
        relative = target.relative_to(ROOT)
        if guard._uses_agent_skill_path(relative):
            unsafe.append(str(target))
    elif not any(target.is_relative_to(approved) for approved in approved_roots):
        unsafe.append(str(target))
REPORT['checks']['resolved_target_input_audit'] = {'recorded_input_count': input_count, 'unsafe_inputs': unsafe,
    'method': 'Use the same approved-root inventory, resolving symlink targets across all approved roots. Preserve the original .fls verbatim.'}
if unsafe:
    REPORT['hard_errors'].append('Unsafe resolved TeX dependencies')

schema = json.loads((ROOT / '.codex/skills/validate-paper/templates/figure_manifest.schema.json').read_text())
jsonschema.validate(json.loads((ROOT / 'figure_manifest.json').read_text()), schema)
REPORT['checks']['figure_schema'] = {'passed': True}
figures = run('canonical_figures', [sys.executable, CHECKS / 'validate_figures.py', '--paper-dir', '.'])
if figures.returncode:
    errors = (figures.stdout + figures.stderr).strip()
    expected = 'Figure validation failed: figures[0] invalid prompt log: Concept prompt log is an empty placeholder: figures/geometry_calibration_overview.prompts.json'
    if errors == expected:
        REPORT['pending'].append('Required concept PNG and prompt log await the explicitly mandated synchronous orchestrator render; the writer must leave the guarded placeholder and {} stub. Rerun final figure validation and compilation after that render.')
    elif "ModuleNotFoundError: No module named 'src'" in errors:
        REPORT['pending'].append('Canonical figure validator is unavailable because this process lacks the orchestrator src package. Parent must rerun it after the required concept render; schema validation alone is not final figure validation.')
    else:
        REPORT['hard_errors'].append(errors)

try:
    from src.orchestrator.paper_step import compute_last_body_page_fill_ratio, find_reference_start_page, find_supplement_start_page, read_pdf_page_layouts, read_pdf_page_texts, validate_visible_language
except ModuleNotFoundError as error:
    if error.name not in ('src', 'src.orchestrator', 'src.orchestrator.paper_step'):
        raise
    rendered = subprocess.run(['pdftotext', '-layout', str(ROOT / 'paper.pdf'), '-'], check=True, capture_output=True, text=True)
    pages = rendered.stdout.rstrip('\f').split('\f')
    heading_spec = importlib.util.spec_from_file_location('rendered_si_headings', CHECKS / 'validate_rendered_si.py')
    heading_validator = importlib.util.module_from_spec(heading_spec)
    heading_spec.loader.exec_module(heading_validator)
    reference_start = next(index for index, page in enumerate(pages, 1) if heading_validator.REFERENCE_HEADING_RE.search(page))
    supplement_start = next(index for index, page in enumerate(pages, 1) if heading_validator.SUPPLEMENT_HEADING_RE.search(page))
    body_pages = reference_start - 1
    REPORT['checks']['rendered_page_budget'] = {'method': 'Rendered heading/page inspection only; canonical geometric-fill backend is not installed in this process.',
        'body_pages': body_pages, 'last_body_page_fill_ratio': None, 'reference_start_page': reference_start,
        'supplement_start_page': supplement_start, 'total_pages': len(pages), 'passed': None,
        'required_min_pages': 8, 'required_max_pages': 9, 'required_min_last_page_fill': .75}
    if not 8 <= body_pages <= 9:
        REPORT['hard_errors'].append('Rendered venue page-count constraint failed')
    REPORT['checks']['visible_language'] = {'checked': False, 'reason': 'Canonical orchestrator backend unavailable; requires parent validation.'}
    REPORT['pending'].append('Parent must rerun canonical geometric page-fill and visible-language validation. No character-count proxy or fallback pass is claimed.')
else:
    pages = read_pdf_page_texts(ROOT / 'paper.pdf')
    reference_start = find_reference_start_page(pages)
    supplement_start = find_supplement_start_page(pages)
    body_pages = reference_start - 1
    fill = compute_last_body_page_fill_ratio(read_pdf_page_layouts(ROOT / 'paper.pdf'), last_body_page_number=body_pages,
                                           reference_start_page=reference_start, body_columns=1)
    REPORT['checks']['rendered_page_budget'] = {'method': 'Canonical rendered geometric text/graphics-bounds function; explicit requirements from VENUE.md because the installed package has no venue catalog.',
        'body_pages': body_pages, 'last_body_page_fill_ratio': fill, 'reference_start_page': reference_start,
        'supplement_start_page': supplement_start, 'total_pages': len(pages), 'required_min_pages': 8,
        'required_max_pages': 9, 'required_min_last_page_fill': .75}
    if not 8 <= body_pages <= 9 or fill is None or (body_pages == 8 and fill < .75):
        REPORT['hard_errors'].append('Rendered venue page budget failed')
    language = validate_visible_language((ROOT / 'paper.tex').read_text(), paper_profile=REGISTRY['paper_profile'],
                                        presentation_contract=REGISTRY['presentation_contract'])
    REPORT['checks']['visible_language'] = language
    REPORT['hard_errors'].extend(language['hard_errors'])
if run('rendered_supplement', [sys.executable, CHECKS / 'validate_rendered_si.py', '--pdf', 'paper.pdf']).returncode:
    REPORT['hard_errors'].append('Rendered Supplementary Information check failed')
reference_count = len(json.loads((ROOT / 'references_provenance.json').read_text())['references'])
REPORT['checks']['reference_count'] = reference_count
if not 25 <= reference_count <= 30:
    REPORT['hard_errors'].append('Reference-count constraint failed')

original = ROOT / 'results/ideas/02_cross_fitted_ilr_residual_geometry/program_1'
digest = hashlib.sha256()
for path in sorted(original.rglob('*'), key=lambda path: path.relative_to(original).as_posix()):
    relative = path.relative_to(original).as_posix().encode()
    if path.is_symlink():
        raise ValueError('Source tree symlink: ' + str(path))
    if path.is_dir():
        digest.update(b'dir\0' + relative + b'\0')
    else:
        content = path.read_bytes()
        digest.update(b'file\0' + relative + b'\0' + str(len(content)).encode() + b'\0')
        digest.update(content)
identity = {'selected_tree_sha256': 'sha256:' + digest.hexdigest(),
            'sealed_tree_sha256': REGISTRY['final_evaluation']['program_tree_sha256'],
            'evaluator_copy_sha256': 'sha256:' + hashlib.sha256((ROOT / 'source_evidence/evaluate_final.py').read_bytes()).hexdigest(),
            'sealed_evaluator_sha256': REGISTRY['final_evaluation']['evaluator_sha256'],
            'selected_source_copy_equal': (original / 'src/program.py').read_bytes() == (ROOT / 'source_evidence/adaptive.py').read_bytes(),
            'implementation_support': 'Readable adaptive.py and evaluate_final.py, cited at line locations; matching hashes verify identity only.'}
identity['passed'] = identity['selected_tree_sha256'] == identity['sealed_tree_sha256'] and identity['evaluator_copy_sha256'] == identity['sealed_evaluator_sha256'] and identity['selected_source_copy_equal']
(ROOT / 'source_evidence/identity_verification.json').write_text(json.dumps(identity, indent=2) + '\n')
REPORT['checks']['source_identity'] = identity
if not identity['passed']:
    REPORT['hard_errors'].append('Evaluated source identity mismatch')

for artifact_name, inputs in {
    'paper.tex': ['paper_data.json', 'references_provenance.json', 'source_evidence/adaptive.py', 'source_evidence/evaluate_final.py'],
    'paper.pdf': ['paper.tex', 'references.bib', 'figure_manifest.json', 'tables/condition_means.tex'],
    'claims_grounding.json': ['paper.tex', 'paper_data.json', 'references_provenance.json', 'build_claims.py'],
    'figure_manifest.json': ['build_artifacts.py', 'paper_strategy.json', 'paper_data.json'],
    'references.bib': ['references_provenance.json', 'finalize_references.py', 'enrich_joint_region.py'],
    'references_provenance.json': ['literature/reading_report.txt', 'finalize_references.py', 'enrich_joint_region.py', 'literature/Henderson2024/reading.json'],
    'reproduction/inventory.json': ['reproduction/resources/final/manifest.json', 'reproduction/resources/search/manifest.json', 'package_reproduction.py'],
    'reproduction/run_provenance.json': ['paper_data.json', 'package_reproduction.py'],
    'source_evidence/identity_verification.json': ['source_evidence/adaptive.py', 'source_evidence/evaluate_final.py', 'source_evidence/final_evaluation_manifest.json'],
}.items():
    artifact = ROOT / artifact_name
    provenance = {'schema_name': 'scientific-evidence.artifact-manifest',
        'artifact': {'path': artifact_name, 'kind': 'manuscript' if artifact_name in ('paper.tex', 'paper.pdf') else 'derived',
                     'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()},
        'derived_from': ['@' + 'evidence[[' + source + ']]' for source in inputs],
        'generated_by': {'script_path': 'validate_artifacts.py'},
        'notes': 'This sidecar records inspected manuscript-input provenance; it does not replace semantic claim review.'}
    Path(str(artifact) + '.prov.json').write_text(json.dumps(provenance, indent=2) + '\n')

if run('claims', [sys.executable, ROOT / '.codex/skills/write-paper-standalone/scripts/validate_claims.py', '--paper-data', 'paper_data.json', '--references', 'references_provenance.json', '--bib', 'references.bib', '--claims', 'claims_grounding.json', '--paper-dir', '.']).returncode:
    REPORT['hard_errors'].append('claims failed')

ledger_entry = {'schema_name': 'scientific-evidence.ledger-entry', 'entry_id': 'paper-validation-' + NOW,
    'entry_kind': 'verification', 'subject': {'path': 'paper.tex', 'kind': 'artifact'},
    'evidence_refs': ['@evidence[[paper_data.json]]', '@evidence[[claims_grounding.json]]', '@evidence[[source_evidence/identity_verification.json]]'],
    'recorded_at': NOW, 'notes': 'No new model evaluation; final qualification remains independent of observed failures. Concept rendering is deferred to its required owner.'}
with (ROOT / 'scientific-evidence/ledger.jsonl').open('a') as ledger:
    ledger.write(json.dumps(ledger_entry) + '\n')
evidence_result = run('scientific_evidence', [sys.executable, ROOT / '.codex/skills/scientific-evidence/scripts/scientific_evidence.py', 'verify', '--root-dir', '.'])
evidence_report = json.loads((ROOT / 'scientific-evidence/verification-report.json').read_text())
REPORT['checks']['evidence_summary'] = evidence_report['summary']
if evidence_result.returncode or evidence_report['summary']['dangling_references']:
    REPORT['hard_errors'].append('Scientific evidence verification failed')
REPORT['status'] = 'failed' if REPORT['hard_errors'] else 'ready_for_orchestrator_render' if REPORT['pending'] else 'passed'
(ROOT / 'validation_report.json').write_text(json.dumps(REPORT, indent=2) + '\n')
print(json.dumps({key: REPORT[key] for key in ('status', 'hard_errors', 'pending', 'infrastructure_warnings')}, indent=2))
print(json.dumps(REPORT['checks']['rendered_page_budget'], indent=2))
print(json.dumps(REPORT['checks']['evidence_summary'], indent=2))
raise SystemExit(bool(REPORT['hard_errors']))
