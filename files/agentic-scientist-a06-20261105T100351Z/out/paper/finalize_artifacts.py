import hashlib
import json
from pathlib import Path


def sidecar(path, kind, inputs):
    artifact = Path(path)
    payload = {'schema_name': 'scientific-evidence.artifact-manifest',
               'artifact': {'path': path, 'kind': kind,
                            'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()},
               'derived_from': ['@' + 'evidence[[' + target + ']]' for target in inputs],
               'generated_by': {'script_path': 'finalize_artifacts.py',
                                'command': ['python', 'finalize_artifacts.py']}}
    if path == 'paper.pdf':
        payload['artifact'].pop('sha256')
        payload['notes'] = 'The PDF is rebuilt after orchestrator-owned overview rendering; input trails are preserved without a prematurely fixed PDF hash.'
    Path(path + '.prov.json').write_text(json.dumps(payload, indent=2) + '\n')


def main():
    sidecar('paper.pdf', 'manuscript', ['paper.tex', 'references.bib', 'iclr2026_conference.sty',
                                       'iclr2026_conference.bst', 'figure_manifest.json', 'claims_grounding.json'])
    sidecar('claims_grounding.json', 'derived', ['paper_data.json', 'analysis/summary.json',
                                              'references_provenance.json', 'build_claims.py'])
    sidecar('figure_manifest.json', 'derived', ['paper_strategy.json', 'paper_data.json', 'build_artifacts.py'])
    if Path('analysis/local_validation.json').exists():
        sidecar('analysis/local_validation.json', 'derived', ['paper.pdf', 'validate_local.py',
                                                            'claims_grounding.json', 'figure_manifest.json'])


if __name__ == '__main__':
    main()
