import concurrent.futures
import datetime
import html
import json
import re
import time
from pathlib import Path

import requests


WORKS = [
    ('Vovk2005', 'Algorithmic Learning in a Random World', None),
    ('Papadopoulos2002', 'Inductive Confidence Machines for Regression', None),
    ('Lei2018', 'Distribution-Free Predictive Inference for Regression', '1604.04173'),
    ('Barber2021Jackknife', 'Predictive inference with the jackknife+', '1905.02928'),
    ('Tibshirani2019', 'Conformal Prediction Under Covariate Shift', '1904.06019'),
    ('Angelopoulos2021', 'A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification', '2107.07511'),
    ('Romano2019', 'Conformalized Quantile Regression', '1905.03222'),
    ('Sesia2020', 'A comparison of some conformal quantile regression methods', '1909.05433'),
    ('Yang2024', 'Selection and Aggregation of Conformal Prediction Sets', None),
    ('Vovk2012', 'Conditional validity of inductive conformal predictors', None),
    ('Lei2014', 'Distribution-free prediction bands for non-parametric regression', None),
    ('Guan2023', 'Localized conformal prediction: A generalized inference framework for conformal prediction', None),
    ('Izbicki2020', 'Flexible Distribution-Free Conditional Predictive Bands Using Density Estimators', None),
    ('Barber2021Limits', 'The limits of distribution-free conditional predictive inference', '1903.04684'),
    ('Gibbs2021', 'Adaptive Conformal Inference Under Distribution Shift', '2106.00170'),
    ('Aitchison1982', 'The Statistical Analysis of Compositional Data', 'doi:10.1111/j.2517-6161.1982.tb01195.x'),
    ('Aitchison1980', 'Logistic-normal distributions: Some properties and uses', None),
    ('Egozcue2003', 'Isometric Logratio Transformations for Compositional Data Analysis', None),
    ('Pawlowsky2015', 'Modeling and Analysis of Compositional Data', 'doi:10.1002/9781119003144'),
    ('Hoerl1970', 'Ridge Regression: Biased Estimation for Nonorthogonal Problems', 'doi:10.1080/00401706.1970.10488634'),
    ('Nadaraya1964', 'On Estimating Regression', None),
    ('Barber2023Beyond', 'Conformal prediction beyond exchangeability', '2202.13415'),
    ('Efron1979', 'Bootstrap Methods: Another Look at the Jackknife', 'doi:10.1214/aos/1176344552'),
    ('Brown2001', 'Interval Estimation for a Binomial Proportion', 'doi:10.1214/ss/1009213286'),
    ('Davison1997', 'Bootstrap Methods and their Application', 'doi:10.1017/CBO9780511802843'),
]


def clean(value):
    return html.unescape(re.sub('<[^>]+>', ' ', value)).strip()


def retrieve(work):
    key, title, locator = work
    cached = Path('literature', key + '.json')
    if cached.exists():
        source = json.loads(cached.read_text())
        normalized = lambda value: re.sub('[^a-z0-9]', '', value.lower().replace('modelling', 'modeling'))
        identity_matches = not locator or not locator.startswith('doi:') or source['record'].get('doi', '').lower() == locator[4:].lower()
        if normalized(source['record']['title']) == normalized(title) and identity_matches:
            record = source['record']
            identity = ('arxiv:' + locator if locator and not locator.startswith('doi:') else
                        'doi:' + record['doi'] if record.get('doi') else 'pmlr:v108/izbicki20a')
            return key, identity, record, source
    time.sleep(1.5)
    if key == 'Izbicki2020':
        url = 'https://proceedings.mlr.press/v108/izbicki20a.html'
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        page = response.text
        abstract = clean(re.search(r'<div[^>]*id="abstract"[^>]*>(.*?)</div>', page, re.S).group(1))
        authors = re.findall(r'<meta name="citation_author" content="([^"]+)"', page)
        first_page = re.search(r'name="citation_firstpage" content="([^"]+)"', page).group(1)
        last_page = re.search(r'name="citation_lastpage" content="([^"]+)"', page).group(1)
        record = {'title': title, 'author': ' and '.join(authors), 'year': '2020',
                  'journal': 'Proceedings of Machine Learning Research', 'volume': '108', 'pages': first_page+'--'+last_page, 'url': url}
        source = {'url': url, 'abstract': abstract, 'citation_key': key, 'expected_title': title,
                  'record': record, 'scope_read': 'Official proceedings abstract, metadata, and BibTeX; no citation links followed.'}
        cached.write_text(json.dumps(source, indent=2))
        return key, 'pmlr:v108/izbicki20a', record, source
    if locator and not locator.startswith('doi:'):
        url = 'https://arxiv.org/abs/' + locator
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        page = response.text
        title_match = re.search(r'<h1[^>]*class="title[^>]*>(.*?)</h1>', page, re.S)
        abstract_match = re.search(r'<blockquote[^>]*class="abstract[^>]*>(.*?)</blockquote>', page, re.S)
        authors_match = re.search(r'<div[^>]*class="authors[^>]*>(.*?)</div>', page, re.S)
        if not (title_match and abstract_match and authors_match):
            raise ValueError('Missing arXiv metadata: ' + key)
        found_title = clean(title_match.group(1)).removeprefix('Title:').strip()
        abstract = clean(abstract_match.group(1)).removeprefix('Abstract:').strip()
        author_names = re.findall(r'<a[^>]*>(.*?)</a>', authors_match.group(1), re.S)
        authors = ' and '.join(clean(author) for author in author_names)
        year = 2000 + int(locator[:2])
        record = {'title': found_title, 'author': authors, 'year': str(year),
                  'journal': 'arXiv preprint arXiv:' + locator, 'url': url}
        identity = 'arxiv:' + locator
        source = {'url': url, 'abstract': abstract, 'scope_read': 'Title, authors, abstract only; no references or citation links followed.'}
    else:
        url = 'https://api.crossref.org/works'
        if locator:
            response = requests.get(url + '/' + locator[4:], timeout=60)
            response.raise_for_status()
            metadata = response.json()['message']
        else:
            for retry in range(3):
                response = requests.get(url, params={'query.title': title, 'rows': 1}, timeout=60)
                if response.status_code != 429:
                    break
                time.sleep(5 * (retry + 1))
            response.raise_for_status()
            metadata = response.json()['message']['items'][0]
        found_title = clean(metadata['title'][0])
        authors = ' and '.join((author.get('given', '') + ' ' + author.get('family', '')).strip()
                               for author in metadata.get('author', []))
        year = metadata.get('published', metadata.get('issued'))['date-parts'][0][0]
        identity = 'doi:' + metadata['DOI']
        record = {'title': found_title, 'author': authors, 'year': str(year), 'doi': metadata['DOI']}
        if metadata.get('publisher'):
            record['publisher'] = metadata['publisher']
        if metadata.get('container-title'):
            record['journal'] = clean(metadata['container-title'][0])
        for field in ('volume', 'issue', 'page'):
            if metadata.get(field):
                record[{'page': 'pages', 'issue': 'number'}.get(field, field)] = metadata[field]
        abstract = clean(metadata.get('abstract', ''))
        source = {'url': response.url, 'abstract': abstract, 'crossref_metadata': metadata,
                  'scope_read': 'Exact-title bibliographic record and abstract when available. Citation network not accessed.'}
        if not abstract:
            try:
                lookup = requests.get('https://api.openalex.org/works/https://doi.org/' + metadata['DOI'], timeout=45)
                if lookup.ok:
                    abstract_index = lookup.json().get('abstract_inverted_index') or {}
                    words = {position: word for word, positions in abstract_index.items() for position in positions}
                    abstract = ' '.join(words[position] for position in sorted(words))
                    source['abstract'] = abstract
                    source['abstract_url'] = lookup.url
            except requests.RequestException:
                pass
    source.update({'citation_key': key, 'expected_title': title, 'record': record})
    Path('literature', key + '.json').write_text(json.dumps(source, indent=2))
    return key, identity, record, source


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        records = list(executor.map(retrieve, WORKS))
    bib_entries = []
    provenance = []
    for key, identity, record, source in records:
        publisher_page = Path('literature', key + '.html')
        if publisher_page.exists() and key in ('Vovk2005', 'Papadopoulos2002', 'Vovk2012', 'Egozcue2003'):
            page = publisher_page.read_text()
            section = re.search(r'<section[^>]*data-title="Abstract".*?</section>', page, re.S)
            description = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', page)
            source['abstract'] = clean(section.group(0)) if section else clean(description.group(1))
            source['scope_read'] = 'Publisher abstract or book overview read; saved HTML. No references or related-article links followed.'
            source['read_artifact'] = str(publisher_page)
            if key == 'Vovk2005':
                structured = [json.loads(block) for block in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S)]
                book = next(block for block in structured if isinstance(block, dict) and 'author' in block)
                record['author'] = ' and '.join(author['name'] for author in book['author'])
        if key == 'Pawlowsky2015':
            source['read_artifact'] = 'literature/Pawlowsky2015-excerpt.pdf'
            source['scope_read'] = 'Publisher book excerpt, introduction pages 1 and 2, read; no references followed.'
        if key in ('Lei2014', 'Guan2023'):
            print_date = source.get('crossref_metadata', {}).get('published-print', {}).get('date-parts')
            if print_date:
                record['year'] = str(print_date[0][0])
        if key == 'Yang2024':
            for field in ('volume', 'number', 'pages'):
                record.pop(field, None)
        if key == 'Vovk2005':
            record['publisher'] = source['crossref_metadata']['publisher']
        Path('literature', key + '.json').write_text(json.dumps(source, indent=2))
        print(key, record['title'], record['year'], '\n', source['abstract'][:2000], '\n')
        kind = 'book' if key in ('Vovk2005', 'Pawlowsky2015', 'Davison1997') else 'article'
        bib_entries.append('@' + kind + '{' + key + ',\n' + '\n'.join(
            '  ' + field + ' = {' + str(value).replace('&', r'\&') + '},'
            for field, value in record.items()) + '\n}\n')
        provenance.append({'id': 'ref.' + key, 'paper_id': identity, 'citation_key': key,
                           'query': source['expected_title'], 'source_url': source['url'],
                           'title': record['title'], 'year': int(record['year']),
                           'read_artifact': source.get('read_artifact', 'literature/' + key + '.json'),
                           'read_scope': source['scope_read']})
    Path('references.bib').write_text('\n'.join(bib_entries))
    Path('references_provenance.json').write_text(json.dumps({
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'count': len(provenance), 'queries': [work[1] for work in WORKS], 'references': provenance,
        'safety': 'Only exact known foundational titles and direct known arXiv identifiers; no joint-topic discovery or citation-network traversal.'}, indent=2))


if __name__ == '__main__':
    main()
