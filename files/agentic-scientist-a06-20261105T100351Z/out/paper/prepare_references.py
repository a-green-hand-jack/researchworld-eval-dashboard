import concurrent.futures
import datetime
import hashlib
import html
import json
import re
import time
from pathlib import Path

import requests


SOURCES = [
    ('Wang2024MMLUPro', 'arxiv', '2406.01574'),
    ('Demsar2006Comparisons', 'jmlr', 'https://www.jmlr.org/papers/v7/demsar06a.html'),
    ('Dietterich1998Tests', 'doi', '10.1162/089976698300017197'),
    ('Polo2024MultiPrompt', 'arxiv', '2405.17202'),
    ('Shi2024BestArm', 'arxiv', '2402.09723'),
    ('Sclar2024Formatting', 'arxiv', '2310.11324'),
    ('Dwork2015Adaptive', 'arxiv', '1411.2664'),
    ('Blum2015Ladder', 'arxiv', '1502.04585'),
    ('Chernozhukov2013Gaussian', 'arxiv', '1212.6906'),
    ('Andrews2018Winners', 'doi', '10.3386/w25456'),
    ('Berk2013PostSelection', 'doi', '10.1214/12-AOS1077'),
    ('Bates2021CrossValidation', 'arxiv', '2104.00673'),
    ('Brown2001Binomial', 'doi', '10.1214/ss/1009213286'),
    ('Efron1979Bootstrap', 'doi', '10.1214/aos/1176344552'),
    ('Stone1974CrossValidation', 'doi', '10.1111/j.2517-6161.1974.tb00994.x'),
    ('Guyon2003Selection', 'jmlr', 'https://www.jmlr.org/papers/v3/guyon03a.html'),
    ('Varoquaux2018CrossValidation', 'doi', '10.1016/j.neuroimage.2017.06.061'),
    ('Nadeau2003Inference', 'doi', '10.1023/A:1024068626366'),
    ('Benjamini1995', 'doi', '10.1111/j.2517-6161.1995.tb02031.x'),
    ('Varma2006Bias', 'doi', '10.1186/1471-2105-7-91'),
    ('Ambroise2002Selection', 'doi', '10.1073/pnas.102102699'),
    ('Arlot2010Survey', 'doi', '10.1214/09-SS054'),
    ('Cawley2010Overfitting', 'jmlr', 'https://www.jmlr.org/papers/v11/cawley10a.html'),
    ('Bengio2004Variance', 'jmlr', 'https://www.jmlr.org/papers/v5/grandvalet04a.html'),
    ('DiCiccio1996Bootstrap', 'doi', '10.1214/ss/1032280214'),
]


def fetch_reference(source):
    citation_key, kind, identifier = source
    directory = Path('literature')
    directory.mkdir(exist_ok=True)
    cached_path = directory / (citation_key + '.json')
    if cached_path.exists() and not (citation_key == 'Varoquaux2018CrossValidation' and json.loads(cached_path.read_text()).get('doi') != identifier):
        content = json.loads(cached_path.read_text())
        title, authors, year, url = (content[field] for field in ['title', 'authors', 'year', 'url'])
        journal = 'Journal of Machine Learning Research' if kind == 'jmlr' else (content.get('metadata', {}).get('container-title') or ['arXiv preprint arXiv:' + identifier if kind == 'arxiv' else 'Working paper'])[0]
        entry = f'@article{{{citation_key},\n title={{{title}}},\n author={{{" and ".join(authors)}}},\n year={{{year}}},\n journal={{{journal}}}\n}}\n'
        extent = 'Original abstract and metadata consulted; see saved abstract. No citation graph followed.' if content.get('abstract') else 'Original publisher landing page and metadata consulted; no citation graph followed.'
        if not content.get('abstract') and content.get('original_status', 200) != 200:
            extent = 'Bibliographic metadata only; original inaccessible. Do not cite substantively.'
        provenance = {'id': 'ref.original.' + citation_key, 'citation_key': citation_key, 'title': title, 'year': int(year), 'source_url': url, 'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'consultation_path': str(cached_path), 'consultation_extent': extent, 'sha256': hashlib.sha256(cached_path.read_bytes()).hexdigest()}
        return entry, provenance
    if kind == 'arxiv':
        url = 'https://arxiv.org/abs/' + identifier
        response = requests.get(url, timeout=60)
        for delay in [2, 5, 10]:
            if response.status_code != 429:
                break
            time.sleep(delay)
            response = requests.get(url, timeout=60)
        response.raise_for_status()
        text = response.text
        title = html.unescape(re.search(r'<meta name="citation_title" content="(.*?)"', text).group(1))
        authors = [html.unescape(author) for author in re.findall(r'<meta name="citation_author" content="(.*?)"', text)]
        year = re.search(r'<meta name="citation_date" content="(\d{4})', text).group(1)
        abstract_match = re.search(r'<blockquote class="abstract[^>]*>(.*?)</blockquote>', text, re.S)
        abstract = html.unescape(re.sub('<[^>]+>', '', abstract_match.group(1))).strip()
        entry = f'@article{{{citation_key},\n title={{{title}}},\n author={{{" and ".join(authors)}}},\n year={{{year}}},\n journal={{arXiv preprint arXiv:{identifier}}}\n}}\n'
        content = {'title': title, 'authors': authors, 'year': year, 'abstract': abstract, 'url': url}
        extent = 'Original arXiv abstract and bibliographic metadata only; no related-paper links or citation graph followed.'
    elif kind == 'doi':
        url = 'https://api.crossref.org/works/' + identifier
        response = requests.get(url, timeout=60)
        for delay in [2, 5, 10]:
            if response.status_code != 429:
                break
            time.sleep(delay)
            response = requests.get(url, timeout=60)
        response.raise_for_status()
        metadata = response.json()['message']
        title = html.unescape(metadata['title'][0])
        authors = [' '.join(filter(None, [author.get('given'), author.get('family')])) for author in metadata.get('author', [])]
        year = str(metadata.get('published', metadata.get('issued'))['date-parts'][0][0])
        abstract = html.unescape(re.sub('<[^>]+>', '', metadata.get('abstract', '')))
        content = {'title': title, 'authors': authors, 'year': year, 'abstract': abstract, 'url': url, 'doi': identifier, 'metadata': metadata}
        journal = metadata.get('container-title', ['Working paper'])[0] if metadata.get('container-title') else 'Working paper'
        entry = f'@article{{{citation_key},\n title={{{title}}},\n author={{{" and ".join(authors)}}},\n year={{{year}}},\n journal={{{journal}}},\n doi={{{identifier}}}\n}}\n'
        extent = 'Original publisher-deposited Crossref abstract and metadata; no citing or related pages accessed.'
        if not abstract:
            original_url = metadata.get('resource', {}).get('primary', {}).get('URL', 'https://doi.org/' + identifier)
            original = requests.get(original_url, timeout=45)
            content['original_status'] = original.status_code
            content['original_url'] = original.url
            if original.ok:
                (directory / (citation_key + '.html')).write_text(original.text)
                extent = 'Original publisher landing page and bibliographic metadata; no citation graph followed.'
            else:
                extent = 'Bibliographic metadata consulted; original page inaccessible. Citation limited to the work named by its title.'
    else:
        url = identifier
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        text = response.text
        title = html.unescape(re.search(r'<meta name="citation_title" content="(.*?)"', text).group(1))
        authors = [html.unescape(author) for author in re.findall(r'<meta name="citation_author" content="(.*?)"', text)]
        year = re.search(r'<meta name="citation_publication_date" content="(\d{4})', text).group(1)
        abstract_match = re.search(r'<(?:div|p) (?:id|class)="abstract"[^>]*>(.*?)</(?:div|p)>', text, re.S)
        if abstract_match is None:
            abstract_match = re.search(r'<h3>Abstract</h3>(.*?)(?:<h3>|<p>|</body>)', text, re.S)
        abstract = html.unescape(re.sub('<[^>]+>', '', abstract_match.group(1))).strip()
        content = {'title': title, 'authors': authors, 'year': year, 'abstract': abstract, 'url': url}
        entry = f'@article{{{citation_key},\n title={{{title}}},\n author={{{" and ".join(authors)}}},\n year={{{year}}},\n journal={{Journal of Machine Learning Research}}\n}}\n'
        extent = 'Original JMLR abstract and metadata; no citation graph followed.'
    local_path = directory / (citation_key + '.json')
    local_path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + '\n')
    provenance = {'id': 'ref.original.' + citation_key, 'citation_key': citation_key, 'title': title, 'year': int(year), 'source_url': url, 'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'consultation_path': str(local_path), 'consultation_extent': extent, 'sha256': hashlib.sha256(local_path.read_bytes()).hexdigest()}
    return entry, provenance


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        results = list(executor.map(fetch_reference, SOURCES))
    Path('references.bib').write_text('\n'.join(entry for entry, provenance in results))
    Path('references_provenance.json').write_text(json.dumps({'count': len(results), 'retrieval_policy': 'Fixed permitted starter identifiers and known foundational originals only. No topical discovery or citation traversal.', 'references': [provenance for entry, provenance in results]}, indent=2) + '\n')
    print('Retrieved', len(results), 'fixed original sources')


if __name__ == '__main__':
    main()
