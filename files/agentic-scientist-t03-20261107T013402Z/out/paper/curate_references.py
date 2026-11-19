import concurrent.futures
import datetime
import json
import re
from pathlib import Path

import requests
from unidecode import unidecode


ENTRIES = [
    ('Lundberg2017', '10.48550/arXiv.1705.07874'),
    ('Krishna2022', '10.48550/arXiv.2202.01602'),
    ('Yuan2022', '10.48550/arXiv.2204.11351'),
    ('Musco2024', '10.48550/arXiv.2410.01917'),
    ('Chen2020', '10.48550/arXiv.2006.16234'),
    ('Marx2020', '10.48550/arXiv.1909.06677'),
    ('Nogueira2018', 'title:On the Stability of Feature Selection Algorithms'),
    ('Webber2010', '10.1145/1852102.1852106'),
    ('Ding2021', '10.48550/arXiv.2108.04884'),
    ('Gorishniy2021', '10.48550/arXiv.2106.11959'),
    ('Lundberg2018', '10.48550/arXiv.1802.03888'),
    ('Owen1972', '10.1287/mnsc.18.5.64'),
    ('Shapley1953', '10.1515/9781400881970-018'),
    ('Castro2009', '10.1016/j.cor.2008.04.004'),
    ('Hoeffding1963', '10.1080/01621459.1963.10500830'),
    ('Maurer2009', '10.48550/arXiv.0907.3740'),
    ('Efron1979', '10.1214/aos/1176344552'),
    ('Breiman2001', '10.1023/A:1010933404324'),
    ('Hosmer2013', '10.1002/9781118548387'),
    ('Pedregosa2011', 'title:Scikit-learn: Machine Learning in Python'),
    ('Harris2020', '10.1038/s41586-020-2649-2'),
    ('Virtanen2020', '10.1038/s41592-019-0686-2'),
    ('Hunter2007', '10.1109/MCSE.2007.55'),
    ('McKinney2010', '10.25080/Majora-92bf1922-00a'),
    ('GermanCredit', '10.24432/C5NC77'),
]


def fetch(entry):
    key, identifier = entry
    fields = 'id,doi,title,publication_year,authorships,abstract_inverted_index,primary_location'
    if identifier.startswith('title:'):
        title = identifier[6:]
        url = 'https://api.openalex.org/works'
        response = requests.get(url, params={'filter': 'title.search:' + title, 'select': fields, 'per-page': 5}, timeout=50)
        response.raise_for_status()
        normalized = lambda text: re.sub(r'[^a-z0-9]', '', text.lower())
        matches = [item for item in response.json()['results'] if normalized(item['title']) == normalized(title)]
        if not matches:
            raise RuntimeError('No exact title match: ' + title)
        record = matches[0]
        url = response.url
    else:
        url = 'https://api.openalex.org/works/https://doi.org/' + identifier
        response = requests.get(url, params={'select': fields}, timeout=50)
        response.raise_for_status()
        record = response.json()
        url = response.url
    abstract_index = record.get('abstract_inverted_index') or {}
    words = {position: word for word, positions in abstract_index.items() for position in positions}
    record['read_abstract'] = ' '.join(words[position] for position in sorted(words))
    record['citation_key'] = key
    record['source_url'] = url
    record['query'] = identifier
    return record


def main():
    directory = Path('literature_evidence')
    directory.mkdir(exist_ok=True)
    records = list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(fetch, ENTRIES))
    references = []
    bib_entries = []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for record in records:
        key = record['citation_key']
        if key == 'Nogueira2018':
            primary_url = 'https://jmlr.org/papers/v18/17-514.bib'
            primary = requests.get(primary_url, timeout=30)
            primary.raise_for_status()
            (directory / 'Nogueira2018.primary.bib').write_text(primary.text)
            record['publication_year'] = 2018
            record['bibliography_primary_url'] = primary_url
        (directory / (key + '.json')).write_text(json.dumps(record, indent=2))
        authors = ' and '.join(unidecode(author['author']['display_name']) for author in record['authorships'])
        if not authors:
            authors = '{UCI Machine Learning Repository}'
        title = record['title'].replace('&', r'\&').replace('_', r'\_')
        venue = (((record.get('primary_location') or {}).get('source') or {}).get('display_name') or 'Preprint or primary record').replace('&', r'\&')
        if 'arxiv.' in record['query'].lower():
            venue = 'arXiv preprint arXiv:' + record['query'].split('.')[-2].split('arXiv.')[-1] + '.' + record['query'].split('.')[-1]
        if key == 'Nogueira2018':
            venue = 'Journal of Machine Learning Research, 18(174):1--54'
        doi = (record.get('doi') or '').replace('https://doi.org/', '')
        bib_entries.append(f'@misc{{{key},\n  title = {{{{{title}}}}},\n  author = {{{authors}}},\n  year = {{{record["publication_year"]}}},\n  howpublished = {{{venue}}},\n  doi = {{{doi}}}\n}}')
        references.append({'id': 'ref.openalex.' + record['id'].rsplit('/', 1)[-1], 'paper_id': record['id'], 'citation_key': key, 'title': record['title'], 'year': record['publication_year'], 'venue': venue, 'query': record['query'], 'source_url': record['source_url'], 'retrieved_at': now, 'local_record': str(directory / (key + '.json')), 'read_scope': 'Primary bibliographic record and abstract when available; no references, citing works, related pages, or full-text search accessed.'})
        print(key, record['title'], 'abstract words', len(record['read_abstract'].split()))
    Path('references.bib').write_text('\n\n'.join(bib_entries) + '\n')
    Path('references_provenance.json').write_text(json.dumps({'generated_at': now, 'count': len(references), 'queries': [identifier for key, identifier in ENTRIES], 'references': references}, indent=2))
    for output in ('references.bib', 'references_provenance.json'):
        sidecar = {'schema_name': 'scientific-evidence.artifact-manifest', 'artifact': {'path': output, 'kind': 'derived'}, 'derived_from': ['@evidence[[' + reference['local_record'] + ']]' for reference in references], 'generated_by': {'script_path': 'curate_references.py'}, 'notes': 'Known primary records and available abstracts only; no citation graph traversal. Nogueira metadata corrected using the retained publisher BibTeX record.'}
        Path(output + '.prov.json').write_text(json.dumps(sidecar, indent=2))


if __name__ == '__main__':
    main()
