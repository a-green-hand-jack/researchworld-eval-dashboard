import concurrent.futures
import json
from pathlib import Path
from retrieve_exact_references import DOIS, get, plain


def consult(item):
    key, doi = item
    path = Path('literature', key + '.json')
    data = json.loads(path.read_text())
    if not data.get('abstract'):
        try:
            response = json.loads(get('https://api.openalex.org/works/https://doi.org/' + doi))
            inverted = response.get('abstract_inverted_index') or {}
            positions = {position: token for token, indices in inverted.items() for position in indices}
            data['abstract'] = ' '.join(positions[index] for index in sorted(positions))
            data['content_source_url'] = 'https://api.openalex.org/works/https://doi.org/' + doi
        except Exception as error:
            data['content_error'] = str(error)
    path.write_text(json.dumps(data, indent=2))
    return key, plain(data.get('abstract') or '')


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for key, content in pool.map(consult, DOIS.items()):
            print(key, content or 'NO ABSTRACT', flush=True)
