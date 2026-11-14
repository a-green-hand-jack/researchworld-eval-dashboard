import concurrent.futures
import datetime
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


DOIS = [
    ('Vovk2005', '10.1007/b106715'),
    ('Papadopoulos2002', '10.1007/3-540-36755-1_29'),
    ('Lei2018', '10.1080/01621459.2017.1307116'),
    ('LeiWasserman2014', '10.1111/rssb.12021'),
    ('Aitchison1982', '10.1111/j.2517-6161.1982.tb01195.x'),
    ('Egozcue2003', '10.1023/A:1023818214614'),
    ('AitchisonShen1980', '10.1093/biomet/67.2.261'),
    ('KoenkerBassett1978', '10.2307/1913643'),
    ('KoenkerHallock2001', '10.1257/jep.15.4.143'),
    ('Friedman2001', '10.1214/aos/1013203451'),
    ('Friedman2002', '10.1016/S0167-9473(01)00065-2'),
    ('Efron1979', '10.1214/aos/1176344552'),
    ('Wilson1927', '10.1080/01621459.1927.10502953'),
    ('HoerlKennard1970', '10.1080/00401706.1970.10488634'),
    ('Stone1974', '10.1111/j.2517-6161.1974.tb00994.x'),
    ('Hastie2009', '10.1007/978-0-387-84858-7'),
]
ARXIV = [
    ('AngelopoulosBates2021', '2107.07511'),
    ('Romano2019', '1905.03222'),
    ('Tibshirani2019', '1904.06019'),
    ('Barber2021', '1905.02928'),
    ('BarberLimits2021', '1903.04684'),
    ('Guan2023', '1908.08558'),
    ('Vovk2012', '1209.2673'),
    ('BarberBeyond2023', '2202.13415'),
]


def clean(value):
    return BeautifulSoup(str(value), 'html.parser').get_text(' ', strip=True)


def retrieve(item):
    key, identifier, mode = item
    if mode == 'doi':
        url = 'https://api.crossref.org/works/' + identifier
        for retry in range(6):
            response = requests.get(url, timeout=60, headers={'User-Agent': 'ScientificLiteratureVerification/1.0'})
            if response.status_code != 429:
                break
            time.sleep(2 ** retry)
        response.raise_for_status()
        metadata = response.json()['message']
        title = clean(metadata['title'][0])
        authors = [' '.join(filter(None, [author.get('given'), author.get('family')]))
                   for author in metadata.get('author', [])]
        if not authors:
            authors_url = 'https://api.openalex.org/works/https://doi.org/' + identifier
            authors_response = requests.get(authors_url, timeout=60)
            authors_response.raise_for_status()
            authors = [item['author']['display_name'] for item in authors_response.json()['authorships']]
        year = metadata.get('published', metadata.get('issued'))['date-parts'][0][0]
        venue = clean((metadata.get('container-title') or [''])[0])
        abstract = clean(metadata.get('abstract', ''))
        fields = dict(title=title, author=' and '.join(authors), year=str(year),
                      doi=identifier, journal=venue)
        if metadata.get('type') == 'book':
            fields.pop('journal')
            fields['publisher'] = metadata.get('publisher', '')
        for field in ['volume', 'issue', 'page']:
            if field in metadata:
                fields[{'issue': 'number', 'page': 'pages'}.get(field, field)] = metadata[field]
        kind = 'book' if metadata.get('type') == 'book' else 'article'
        consulted = 'Crossref title, author, venue and abstract fields only; no citation networks accessed'
        saved = dict(metadata=metadata, consulted_abstract=abstract)
    else:
        url = 'https://arxiv.org/abs/' + identifier
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.select_one('h1.title').get_text(' ', strip=True).removeprefix('Title:').strip()
        authors = [tag.get_text(strip=True) for tag in soup.select('.authors a')]
        abstract = soup.select_one('blockquote.abstract').get_text(' ', strip=True).removeprefix('Abstract:').strip()
        date = soup.select_one('.dateline').get_text(' ', strip=True)
        year = int(re.search(r'20\d{2}', date).group())
        venue = 'arXiv preprint arXiv:' + identifier
        fields = dict(title=title, author=' and '.join(authors), year=str(year), journal=venue)
        kind = 'article'
        consulted = 'Direct known arXiv identifier; read title, authors and abstract only; no references or related-page links accessed'
        saved = dict(title=title, authors=authors, abstract=abstract, date=date)
    fields = {field: str(value).replace('&', r'\&') for field, value in fields.items() if value}
    bibtex = '@' + kind + '{' + key + ',\n' + ',\n'.join(
        '  ' + field + ' = {' + value + '}' for field, value in fields.items()) + '\n}\n'
    path = Path('literature_evidence') / (key + '.json')
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(saved, indent=2, ensure_ascii=False) + '\n')
    record = dict(id='ref.' + key, paper_id=identifier, citation_key=key, title=title,
                  year=year, venue=venue, query='Direct verified foundational identifier: ' + identifier,
                  source_url=url, retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  consulted_content=consulted, content_path=str(path))
    return bibtex, record


def main():
    items = [(key, identifier, 'doi') for key, identifier in DOIS]
    items += [(key, identifier, 'arxiv') for key, identifier in ARXIV]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(retrieve, items))
    url = 'https://jmlr.org/papers/v7/meinshausen06a.html'
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.get_text(' ', strip=True)
    Path('literature_evidence/Meinshausen2006.txt').write_text(content)
    results.append(('@article{Meinshausen2006,\n  author={Nicolai Meinshausen},\n'
                    '  title={Quantile Regression Forests},\n  journal={Journal of Machine Learning Research},\n'
                    '  volume={7},\n  pages={983--999},\n  year={2006}\n}\n',
                    dict(id='ref.Meinshausen2006', paper_id=url, citation_key='Meinshausen2006',
                         title='Quantile Regression Forests', year=2006, query='Direct known JMLR article',
                         source_url=url, consulted_content='Article landing-page abstract',
                         content_path='literature_evidence/Meinshausen2006.txt')))
    Path('references.bib').write_text('\n'.join(result[0] for result in results))
    Path('references_provenance.json').write_text(json.dumps(dict(
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), count=len(results),
        queries=[result[1]['query'] for result in results], references=[result[1] for result in results]),
        indent=2, ensure_ascii=False) + '\n')
    for _, record in results:
        saved = Path(record['content_path']).read_text()
        data = json.loads(saved) if saved.startswith('{') else {'abstract': saved}
        print(record['citation_key'], record['title'], record['year'])
        print(str(data.get('abstract', data.get('consulted_abstract', 'No abstract supplied.')))[:2800])


if __name__ == '__main__':
    main()
