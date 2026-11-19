import json
from pathlib import Path


def record(path, kind, inputs, script, command):
    provenance = {'schema_name': 'scientific-evidence.artifact-manifest',
                  'artifact': {'path': path, 'kind': kind}, 'derived_from': inputs,
                  'generated_by': {'script_path': script, 'command': command}}
    Path(path+'.prov.json').write_text(json.dumps(provenance, indent=2))


def main():
    record('claims_grounding.json', 'derived', ['@evidence[[paper_data.json]]', '@evidence[[analysis_summary.json]]',
           '@evidence[[references_provenance.json]]', '@evidence[[source_evidence/index.json]]'], 'build_claims.py', ['python', 'build_claims.py'])
    record('figure_manifest.json', 'derived', ['@evidence[[paper_strategy.json]]', '@evidence[[analysis_summary.json]]'],
           'build_artifacts.py', ['python', 'build_artifacts.py'])
    record('source_evidence/index.json', 'derived', ['@evidence[[source_evidence/program.py]]', '@evidence[[source_evidence/evaluate_final.py]]',
           '@evidence[[source_evidence/resource_manifest.json]]', '@evidence[[source_evidence/baseline_source_provenance.json]]'],
           'record_source_provenance.py', ['python', 'record_source_provenance.py'])
    record('paper.pdf', 'manuscript', ['@evidence[[paper.tex]]', '@evidence[[references.bib]]', '@evidence[[iclr2026_conference.sty]]',
           '@evidence[[figures/paired_width_comparison.pdf]]', '@evidence[[figures/coverage_with_uncertainty.pdf]]',
           '@evidence[[figures/fixed_resource_overview.png]]'], '.codex/skills/validate-paper/scripts/validate_compile_inputs.py',
           ['python', '.codex/skills/validate-paper/scripts/validate_compile_inputs.py', 'run', '--', 'pdflatex', '-recorder', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'paper.tex'])
    print('Recorded manuscript, mapping, figure-manifest and source-index provenance.')


if __name__ == '__main__':
    main()
