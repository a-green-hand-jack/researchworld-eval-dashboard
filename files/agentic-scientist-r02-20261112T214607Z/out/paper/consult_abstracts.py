import json
import time
from pathlib import Path

import requests


provenance = json.loads(Path('references_provenance.json').read_text())
for record in provenance['references']:
    path = Path(record['content_path'])
    if path.suffix != '.json':
        continue
    data = json.loads(path.read_text())
    if 'metadata' not in data or data.get('consulted_abstract'):
        continue
    identifier = record['paper_id']
    url = 'https://api.openalex.org/works/https://doi.org/' + identifier
    response = requests.get(url, timeout=40)
    if response.status_code != 200:
        print(record['citation_key'], response.status_code)
        continue
    metadata = response.json()
    inverted = metadata.get('abstract_inverted_index') or {}
    ordered = sorted((position, word) for word, positions in inverted.items() for position in positions)
    abstract = ' '.join(word for position, word in ordered)
    data['consulted_abstract'] = abstract
    data['abstract_source_url'] = url
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    record['consulted_content'] += '; direct DOI OpenAlex abstract, where supplied'
    print(record['citation_key'], metadata.get('title'), '\n', abstract or 'No abstract available')
    time.sleep(.3)
Path('references_provenance.json').write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + '\n')
