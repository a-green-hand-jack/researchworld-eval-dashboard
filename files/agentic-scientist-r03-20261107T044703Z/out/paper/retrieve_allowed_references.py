import concurrent.futures
import datetime
import json
import re
from pathlib import Path
import requests

RECORDS = [
    ('MTEB', 'ARXIV:2210.07316'), ('MMLU', 'ARXIV:2009.03300'),
    ('HELM', 'ARXIV:2211.09110'), ('Tiny', 'ARXIV:2402.14992'),
    ('Metabench', 'ARXIV:2407.12844'), ('BenchBench', 'ARXIV:2407.13696'),
    ('Observational', 'ARXIV:2405.10938'), ('Sloth', 'ARXIV:2412.06540'),
    ('Koren', 'DOI:10.1109/MC.2009.263'), ('Hu', 'DOI:10.1109/ICDM.2008.22'),
    ('CandesRecht', 'DOI:10.1007/s10208-009-9045-5'),
    ('CandesTao', 'DOI:10.1109/TIT.2010.2044061'),
    ('Keshavan', 'DOI:10.1109/TIT.2010.2046205'),
    ('Mazumder', 'TITLE:Spectral Regularization Algorithms for Learning Large Incomplete Matrices'),
    ('PMF', 'TITLE:Probabilistic Matrix Factorization'), ('Jain', 'ARXIV:1212.0467'),
    ('BayesianMF', 'DOI:10.1145/1390156.1390267'),
    ('Efron', 'DOI:10.1214/aos/1176344552'),
    ('Rubin', 'DOI:10.1093/biomet/63.3.581'),
    ('Schafer', 'DOI:10.1037/1082-989X.7.2.147'),
    ('Owen', 'DOI:10.1214/12-AOAS547'),
    ('Hoerl', 'DOI:10.1080/00401706.1970.10488634'),

    ('Chaloner', 'DOI:10.1214/ss/1177009939'),
    ('Cohn', 'DOI:10.1613/jair.295'),

    ('Dempster', 'DOI:10.1111/j.2517-6161.1977.tb01600.x')]

def fetch(record):
    key, identifier = record
    if identifier.startswith('TITLE:'):
        url = 'https://api.semanticscholar.org/graph/v1/paper/search/match'
        response = requests.get(url, params={'query': identifier[6:], 'fields': 'title,paperId,authors,year,abstract,citationStyles'}, timeout=60)
        response.raise_for_status()
        data = response.json()['data'][0]
        assert data['title'].lower().replace('-', ' ') == identifier[6:].lower().replace('-', ' '), data['title']
        abstract = data.get('abstract') or ''
        if not abstract and key == 'PMF':
            import fitz
            pdf = requests.get('https://www.cs.toronto.edu/~amnih/papers/pmf.pdf', timeout=60)
            pdf.raise_for_status()
            document = fitz.open(stream=pdf.content, filetype='pdf')
            abstract = '\n'.join(page.get_text() for page in document)
        bib = re.sub(r'(@\w+\{)[^,]+', lambda match: match.group(1) + key, data['citationStyles']['bibtex'], count=1)
        return key, data['paperId'], response.url, data, bib, abstract
    url = 'https://api.semanticscholar.org/graph/v1/paper/' + identifier
    response = requests.get(url, params={'fields': 'paperId,title,authors,year,abstract,venue,citationStyles'}, timeout=60)
    if response.status_code == 200:
        data = response.json()
        bib = data.get('citationStyles', {}).get('bibtex', '')
        if bib and data.get('abstract') and key != 'Dempster':
            bib = re.sub(r'(@\w+\{)[^,]+', lambda match: match.group(1) + key, bib, count=1)
            return key, identifier, url, data, bib, data['abstract']
    if identifier.startswith('DOI:'):
        url = 'https://api.openalex.org/works/https://doi.org/' + identifier[4:]
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        sequence = {position: word for word, indexes in (data.get('abstract_inverted_index') or {}).items() for position in indexes}
        abstract = ' '.join(sequence[index] for index in sorted(sequence))
        authors = ' and '.join(item['author']['display_name'] for item in data['authorships'])
        bib = '@article{' + key + ',\n title = {' + data['title'].replace('&', r'\&') + '},\n author = {' + authors + '},\n year = {' + str(data['publication_year']) + '},\n doi = {' + identifier[4:] + '}\n}'
        return key, identifier, url, data, bib, abstract
    import xml.etree.ElementTree as element_tree
    url = 'https://export.arxiv.org/api/query?id_list=' + identifier.split(':')[1]
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    entry = element_tree.fromstring(response.text).find('{http://www.w3.org/2005/Atom}entry')
    def text(name):
        return ' '.join(entry.find('{http://www.w3.org/2005/Atom}' + name).text.split())
    authors = ' and '.join(item.find('{http://www.w3.org/2005/Atom}name').text for item in entry.findall('{http://www.w3.org/2005/Atom}author'))
    data = {'title': text('title'), 'year': int(text('published')[:4]), 'abstract': text('summary')}
    bib = '@article{' + key + ',\n title = {' + data['title'] + '},\n author = {' + authors + '},\n year = {' + str(data['year']) + '},\n journal = {arXiv preprint arXiv:' + identifier.split(':')[1] + '}\n}'
    return key, identifier, url, data, bib, data['abstract']

def complete_entry(bib, data, identifier):
    if identifier.startswith('ARXIV:') and re.match(r'@(?:inproceedings|conference)', bib, re.IGNORECASE) and not re.search(r'\bbooktitle\s*=', bib, re.IGNORECASE):
        bib = re.sub(r'^@\w+', '@article', bib)
    location = data.get('primary_location') or {}
    venue = data.get('venue') or (location.get('source') or {}).get('display_name')
    booktitle = re.search(r'booktitle\s*=\s*\{([^}]+)\}', bib, re.IGNORECASE)
    if booktitle:
        venue = booktitle.group(1)
    if not venue and identifier.startswith('ARXIV:'):
        venue = 'arXiv preprint arXiv:' + identifier.split(':')[1]
    if venue and re.match(r'@article', bib, re.IGNORECASE) and not re.search(r'\bjournal\s*=', bib, re.IGNORECASE):
        bib = bib.rstrip().rstrip('}').rstrip().rstrip(',') + ',\n journal = {' + venue + '}\n}'
    return bib


def main():
    directory = Path('literature')
    directory.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    references, entries = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        for key, identifier, url, data, bib, abstract in executor.map(fetch, RECORDS):
            (directory / (key + '.json')).write_text(json.dumps(data, indent=2))
            (directory / (key + '.txt')).write_text(abstract)
            entries.append(complete_entry(bib, data, identifier))
            references.append({'id': 'ref.allowed.' + key, 'paper_id': identifier, 'citation_key': key,
                'title': data['title'], 'year': data.get('year', data.get('publication_year')),
                'query': identifier, 'source_url': url, 'retrieved_at': timestamp,
                'content_path': 'literature/' + key + '.txt',
                'read_scope': 'full PDF' if key == 'PMF' else 'abstract'})
            print(key, data['title'], 'abstract words', len(abstract.split()), flush=True)
    Path('references.bib').write_text('\n\n'.join(entries) + '\n')
    Path('references_provenance.json').write_text(json.dumps({'generated_at': timestamp,
        'count': len(references), 'queries': [identifier for key, identifier in RECORDS],
        'references': references, 'restriction_policy': 'Exact permitted starter IDs and foundational method DOIs only; no citation graphs or broad benchmark searches.'}, indent=2))

if __name__ == '__main__':
    main()
