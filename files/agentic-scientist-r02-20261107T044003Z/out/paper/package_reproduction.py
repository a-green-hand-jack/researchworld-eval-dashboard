import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
inventory = []
for split in ('final', 'search'):
    source = ROOT / 'task' / 'resources' / split
    target = ROOT / 'reproduction' / 'resources' / split
    target.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((source / 'manifest.json').read_text())
    files = [source / 'manifest.json'] + [source / row['file'] for row in manifest['datasets']]
    for original in files:
        destination = target / original.name
        shutil.copyfile(original, destination)
        checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
        expected = next((row['sha256'] for row in manifest['datasets'] if row['file'] == original.name), None)
        if expected is not None and checksum != expected:
            raise ValueError('Frozen resource checksum mismatch: ' + str(destination))
        inventory.append({'path': str(destination.relative_to(ROOT)), 'sha256': checksum,
                          'original': str(original.relative_to(ROOT))})
(ROOT / 'reproduction' / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
registry = json.loads((ROOT / 'paper_data.json').read_text())
final = registry['final_evaluation']
run_provenance = {key: final[key] for key in ('status', 'outcome', 'evaluator_sha256',
                 'program_tree_sha256', 'results_tree_sha256', 'task_tree_sha256')}
run_provenance['qualification_sources'] = ['final.qualification.status', 'final.qualification.outcome', 'final.qualification.correct']
run_provenance['evidence_registry_sha256'] = hashlib.sha256((ROOT / 'paper_data.json').read_bytes()).hexdigest()
(ROOT / 'reproduction' / 'run_provenance.json').write_text(json.dumps(run_provenance, indent=2) + '\n')
shutil.copyfile(ROOT.parent / 'final_evaluation' / 'final_manifest.json', ROOT / 'source_evidence' / 'final_evaluation_manifest.json')
print(f'Packaged {len(inventory)} frozen source resources without running an evaluation.')
