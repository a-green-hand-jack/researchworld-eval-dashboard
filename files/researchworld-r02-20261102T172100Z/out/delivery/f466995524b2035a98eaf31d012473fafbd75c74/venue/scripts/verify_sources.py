"""Verify archived inputs and unmodified selected template files, offline."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

root = Path(__file__).resolve().parents[1]
frozen = []
for p in sorted(Path('/initial-state/inputs/0').glob('*.md')):
    b = p.read_bytes()
    frozen.append(dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
logs = json.loads((root/'sources/fetch-log.json').read_text()) + json.loads((root/'sources/fetch-log-followup.json').read_text())
assets = []
for p in sorted((root/'official/neurips2026').glob('*')):
    b = p.read_bytes()
    assets.append(dict(path=str(p.relative_to(root)), bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), modified_from_upstream=False))
with zipfile.ZipFile(root/'sources/neurips2026_template.zip') as z:
    for a in assets:
        assert z.read(Path(a['path']).name) == (root/a['path']).read_bytes()
for source in logs:
    if 'path' in source:
        b = (root/source['path']).read_bytes()
        assert hashlib.sha256(b).hexdigest() == source['sha256'], source['path']
text = (root/'official/neurips2026/checklist.tex').read_text().split('%%% END INSTRUCTIONS %%%', 1)[1]
heads = re.findall(r'\\item \{\\bf ([^}]+)\}', text)
assert len(heads) == 16, heads
record = {
    'schema_version': 1,
    'verified_on_utc': '2026-11-02',
    'selected_venue': 'NeurIPS 2026 main track',
    'format': 'anonymous submission',
    'content_page_limit': 9,
    'official_call_url': 'https://neurips.cc/Conferences/2026/CallForPapers',
    'official_template_url': 'https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip',
    'official_handbook_url': 'https://neurips.cc/Conferences/2026/MainTrackHandbook',
    'frozen_inputs': frozen,
    'retrievals': logs,
    'selected_unmodified_assets': assets,
    'official_checklist_headings': heads,
    'prohibited_content_incidents_for_venue_only': [],
    'project_wide_incident_status': 'Not established by venue; report owner must aggregate all source-access owners.'
}
# Verify without mutating the archived provenance. Frozen inputs may be absent outside this world.
manifest = json.loads((root/'source-manifest.json').read_text())
for key in ['selected_unmodified_assets', 'official_checklist_headings', 'retrievals']:
    assert record[key] == manifest[key], key
if frozen:
    assert frozen == manifest['frozen_inputs'], 'Frozen input hashes differ from the objective provenance'
print('Verified 3 official assets byte-for-byte, retrieval hashes, and 16 checklist headings.')
