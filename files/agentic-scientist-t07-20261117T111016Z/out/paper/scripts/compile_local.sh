#!/bin/sh
set -eu
python .codex/skills/validate-paper/scripts/validate_compile_inputs.py run -- \
    pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
python .codex/skills/validate-paper/scripts/validate_compile_inputs.py bibtex --paper-dir . --aux paper.aux
python .codex/skills/validate-paper/scripts/validate_compile_inputs.py run -- bibtex paper
python .codex/skills/validate-paper/scripts/validate_compile_inputs.py run -- \
    pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
python .codex/skills/validate-paper/scripts/validate_compile_inputs.py run -- \
    pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
python .codex/skills/validate-paper/scripts/validate_rendered_si.py --pdf paper.pdf
python - <<'PY'
import json
from pathlib import Path
sidecar = dict(schema_name='scientific-evidence.artifact-manifest',
               artifact=dict(path='paper.pdf', kind='manuscript'),
               derived_from=['paper.tex', 'references.bib', 'tables/aggregate.tex',
                             'figures/score_prediction_overview.png',
                             'figures/paired_error_comparison.pdf',
                             'figures/case_budget_reversals.pdf', 'figures/budget_sensitivity.pdf'],
               generated_by=dict(script_path='scripts/compile_local.sh'),
               notes='Input dependency trail; the conceptual overview remains orchestrator-owned and is preserved by this compilation.')
sidecar['derived_from'] = ['@' + 'evidence' + '[' * 2 + target + ']' * 2 for target in sidecar['derived_from']]
Path('paper.pdf.prov.json').write_text(json.dumps(sidecar, indent=2) + '\n')
sidecar = dict(schema_name='scientific-evidence.artifact-manifest',
               artifact=dict(path='paper.tex', kind='manuscript'),
               derived_from=['paper_data.json', 'analysis/paper_statistics.json',
                             'references_provenance.json', 'source_evidence/inventory.json'],
               notes='Evidence inputs for agent-authored manuscript; not an assertion of automatic text generation by a script.')
sidecar['derived_from'] = ['@' + 'evidence' + '[' * 2 + target + ']' * 2 for target in sidecar['derived_from']]
Path('paper.tex.prov.json').write_text(json.dumps(sidecar, indent=2) + '\n')
PY
