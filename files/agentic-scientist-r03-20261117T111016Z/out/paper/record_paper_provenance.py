import json
from pathlib import Path


def write_sidecar(path, kind, sources, script):
    payload = dict(schema_name='scientific-evidence.artifact-manifest',
                   artifact=dict(path=path, kind=kind),
                   derived_from=['@evidence' + '[[' + source + ']]' for source in sources],
                   generated_by=dict(script_path=script))
    Path(path + '.prov.json').write_text(json.dumps(payload, indent=2))


def main():
    references = json.loads(Path('references_provenance.json').read_text())['references']
    literature = [reference['evidence_path'] for reference in references]
    write_sidecar('references.bib', 'derived', literature + ['literature_evidence/Bengio2004_publisher.html'], 'retrieve_paper_references.py')
    write_sidecar('references_provenance.json', 'derived', literature, 'retrieve_paper_references.py')
    write_sidecar('claims_grounding.json', 'derived', ['paper_data.json', 'references_provenance.json', 'source_evidence_manifest.json', 'build_claims.py'], 'build_claims.py')
    write_sidecar('figure_manifest.json', 'derived', ['paper_strategy.json', 'iclr2026_conference.sty', 'build_paper_artifacts.py'], 'build_paper_artifacts.py')
    write_sidecar('local_validation_report.json', 'derived', ['paper.pdf', 'paper.tex', 'paper.fls', 'figure_manifest.json', 'check_paper_locally.py'], 'check_paper_locally.py')
    write_sidecar('paper.pdf', 'manuscript', ['paper.tex', 'references.bib', 'iclr2026_conference.sty', 'figures/method_overview.png', 'figures/budget_comparison.pdf', 'figures/history_structure_controls.pdf', 'tables/main_comparison.tex'], 'compile_paper_locally.sh')


if __name__ == '__main__':
    main()
