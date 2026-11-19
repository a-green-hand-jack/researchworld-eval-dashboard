import concurrent.futures
import json
import pathlib
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parent


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'GroundedPaper/1.0'}), timeout=45) as response:
        return response.read()


def complete(path):
    record = json.loads(path.read_text())
    data = record['data']
    if path.stem == 'Mazumder2010Spectral':
        url = 'https://jmlr.org/papers/v11/mazumder10a.html'
        html = fetch(url).decode()
        soup = BeautifulSoup(html, 'html.parser')
        record = {'citation_key': path.stem, 'identifier': 'jmlr:v11:mazumder10a',
                  'provider': 'JMLR original', 'source_url': url,
                  'retrieved_at': record['retrieved_at'], 'data': {'html_text': soup.get_text(' ', strip=True),
                  'metadata': {tag.get('name'): tag.get('content') for tag in soup.find_all('meta')}}}
        path.write_text(json.dumps(record, indent=2) + '\n')
        print(path.stem, record['data']['html_text'][:150], flush=True)
        return
    doi = data.get('doi', '').replace('https://doi.org/', '') or data.get('externalIds', {}).get('DOI')
    if doi:
        try:
            url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi, safe='')
            crossref = json.loads(fetch(url))['message']
            record['crossref'] = crossref
            record['crossref_url'] = url
            if crossref.get('abstract'):
                record['read_abstract'] = BeautifulSoup(crossref['abstract'], 'html.parser').get_text(' ', strip=True)
        except Exception as error:
            print('crossref failed', path.stem, error, flush=True)
    abstract = record.get('read_abstract') or data.get('abstract')
    if not abstract and data.get('abstract_inverted_index'):
        indexed = {position: word for word, positions in data['abstract_inverted_index'].items() for position in positions}
        abstract = ' '.join(indexed[position] for position in sorted(indexed))
    if path.stem == 'Dempster1977EM':
        abstract = record.get('read_abstract')
        record['discarded_provider_abstract'] = 'Unrelated mechanical-device abstract; not used.'
    if abstract:
        record['read_abstract'] = abstract
    path.write_text(json.dumps(record, indent=2) + '\n')
    print(path.stem, 'ABSTRACT' if abstract else 'NEEDS ORIGINAL', flush=True)


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(complete, sorted((ROOT / 'literature/records').glob('*.json'))))
