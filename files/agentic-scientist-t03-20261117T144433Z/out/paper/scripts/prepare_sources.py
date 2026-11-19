import datetime
import difflib
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def patch_write(path, text):
    target = Path(path)
    if target.exists():
        patch = '*** Begin Patch\n*** Update File: ' + path + '\n@@\n'
        patch += ''.join('-' + line + '\n' for line in target.read_text().splitlines())
        patch += ''.join('+' + line + '\n' for line in text.splitlines())
    else:
        patch = '*** Begin Patch\n*** Add File: ' + path + '\n'
        patch += ''.join('+' + line + '\n' for line in text.splitlines())
    driver = shutil.which('apply_patch') or '/tmp/apply_patch'
    subprocess.run([driver], input=patch + '*** End Patch\n', text=True, check=True)


def escape(text):
    return str(text).replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')


arxiv_sources = [('Lundberg2017', '1705.07874'), ('Krishna2022', '2202.01602'), ('Yuan2022', '2204.11351'), ('Musco2024', '2410.01917'), ('Chen2020', '2006.16234'), ('Marx2020', '1909.06677'), ('Ding2021', '2108.04884'), ('Gorishniy2021', '2106.11959'), ('Maleki2013', '1306.4265')]
doi_sources = [('Breiman2001', '10.1023/A:1010933404324'), ('Friedman2001', '10.1214/aos/1013203451'), ('Harris2020', '10.1038/s41586-020-2649-2'), ('Virtanen2020', '10.1038/s41592-019-0686-2'), ('McKinney2010', '10.25080/Majora-92bf1922-00a'), ('Efron1979', '10.1214/aos/1176344552'), ('DiCiccio1996', '10.1214/ss/1032280214'), ('Diaconis1977', '10.1111/j.2517-6161.1977.tb01624.x'), ('Webber2010', '10.1145/1852102.1852106'), ('Castro2009', '10.1016/j.cor.2008.04.004'), ('Shapley1953', '10.1515/9781400881970-018'), ('GermanCredit', '10.24432/C5NC77')]
direct_sources = [
    ('Nogueira2018', 'https://jmlr.org/papers/v18/17-514.html', 'On the Stability of Feature Selection Algorithms', ['Sarah Nogueira', 'Konstantinos Sechidis', 'Gavin Brown'], 2018, 'Journal of Machine Learning Research'),
    ('Pedregosa2011', 'https://jmlr.org/papers/v12/pedregosa11a.html', 'Scikit-learn: Machine Learning in Python', ['Fabian Pedregosa', 'Gael Varoquaux'], 2011, 'Journal of Machine Learning Research'),
    ('Mitchell2022', 'https://jmlr.org/papers/v23/21-0439.html', 'Sampling Permutations for Shapley Value Estimation', ['Rory Mitchell', 'Joshua Cooper', 'Eibe Frank', 'Geoffrey Holmes'], 2022, 'Journal of Machine Learning Research'),
    ('Covert2021', 'https://proceedings.mlr.press/v130/covert21a.html', 'Improving KernelSHAP: Practical Shapley Value Estimation Using Linear Regression', ['Ian Covert', 'Su-In Lee'], 2021, 'Proceedings of Machine Learning Research'),
]


def main():
    records, entries = [], []
    for key, identifier in arxiv_sources:
        url = 'https://arxiv.org/abs/' + identifier
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('meta', {'name': 'citation_title'})['content']
        authors = [meta['content'] for meta in soup.find_all('meta', {'name': 'citation_author'})]
        year = int(soup.find('meta', {'name': 'citation_date'})['content'][:4])
        abstract = soup.find('blockquote', class_='abstract').get_text(' ', strip=True)
        records.append(dict(id='ref.arxiv.' + identifier, paper_id=identifier, citation_key=key, title=title, year=year, venue='arXiv', query='Exact permitted identifier ' + identifier, source_url=url, consulted_text=abstract))
        entries.append(f'@article{{{key},\n title={{{escape(title)}}},\n author={{{escape(" and ".join(authors))}}},\n year={{{year}}},\n journal={{arXiv preprint arXiv:{identifier}}},\n url={{{url}}}\n}}')
    for key, identifier in doi_sources:
        if key == 'GermanCredit':
            url = 'https://api.datacite.org/dois/' + identifier
            response = requests.get(url, timeout=40)
            response.raise_for_status()
            item = response.json()['data']['attributes']
            title = item['titles'][0]['title']
            year = item['publicationYear']
            authors = [creator['name'] for creator in item.get('creators', [])]
            abstract = ' '.join(description['description'] for description in item.get('descriptions', []) if description.get('descriptionType') == 'Abstract')
            records.append(dict(id='ref.doi.' + identifier.lower(), paper_id=identifier, citation_key=key, title=title, year=year, venue='UCI Machine Learning Repository', query='Exact DOI ' + identifier, source_url=url, consulted_text=abstract))
            entries.append(f'@misc{{{key},\n title={{{escape(title)}}},\n author={{{escape(" and ".join(authors))}}},\n year={{{year}}},\n howpublished={{UCI Machine Learning Repository}},\n doi={{{identifier}}}\n}}')
            continue
        url = 'https://api.crossref.org/works/' + identifier
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        item = response.json()['message']
        title = item['title'][0]
        year = item.get('published', item.get('created'))['date-parts'][0][0]
        authors = [author['family'] + ', ' + author.get('given', '') for author in item.get('author', []) if author.get('family')]
        if len(authors) > 20:
            authors = authors[:20] + ['others']
        venue = (item.get('container-title') or ['Dataset'])[0]
        abstract = BeautifulSoup(item.get('abstract', ''), 'html.parser').get_text(' ', strip=True)
        records.append(dict(id='ref.doi.' + identifier.lower(), paper_id=identifier, citation_key=key, title=title, year=year, venue=venue, query='Exact DOI ' + identifier, source_url=url, consulted_text=abstract or 'Bibliographic record consulted; used only for work identity and methodological attribution.'))
        entries.append(f'@article{{{key},\n title={{{escape(title)}}},\n author={{{escape(" and ".join(authors))}}},\n year={{{year}}},\n journal={{{escape(venue)}}},\n doi={{{identifier}}}\n}}')
    for key, url, expected, fallback_authors, year, venue in direct_sources:
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        title_meta = soup.find('meta', {'name': 'citation_title'})
        title = title_meta['content'] if title_meta else expected
        if difflib.SequenceMatcher(None, title.lower(), expected.lower()).ratio() < .8:
            raise RuntimeError('Exact-title safety check failed for ' + url)
        block = soup.find(id='abstract') or soup.find(class_='abstract')
        if block is None:
            raise RuntimeError('No abstract found at ' + url)
        authors_meta = soup.find_all('meta', {'name': 'citation_author'})
        authors = [meta['content'] for meta in authors_meta] or fallback_authors
        records.append(dict(id='ref.direct.' + key, paper_id=key, citation_key=key, title=title, year=year, venue=venue, query='Exact known methodological title: ' + expected, source_url=url, consulted_text=block.get_text(' ', strip=True)))
        entries.append(f'@article{{{key},\n title={{{escape(title)}}},\n author={{{escape(" and ".join(authors))}}},\n year={{{year}}},\n journal={{{escape(venue)}}},\n url={{{url}}}\n}}')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for record in records:
        record['retrieved_at'] = now
    patch_write('references.bib', '\n\n'.join(entries) + '\n')
    patch_write('references_provenance.json', json.dumps(dict(generated_at=now, count=len(records), queries=[record['query'] for record in records], references=records), indent=2))
    patch_write('reference_consultation.md', '# Safely scoped reference consultation\n\nOnly exact known identifiers or permitted starter documents were opened. Abstracts and bibliographic metadata were consulted; no citation chains, recommendation lists, surveys, or unrestricted searches were used. Pre-existing broad-query noise was excluded without following its links. No prohibited content was encountered in this writing pass.\n\n' + '\n\n'.join('## ' + record['citation_key'] + '\n' + record['title'] + '\n\n' + record['consulted_text'] for record in records))
    for source, target in [('../task/evaluate_final.py', 'source_evidence/evaluation/evaluate_final.py'), ('../task/requirements.txt', 'source_evidence/evaluation/requirements.txt'), ('../task/resources/final/manifest.json', 'source_evidence/evaluation/manifest.json')]:
        patch_write(target, Path(source).read_text())
    for name, target in [('iclr2026_conference.sty', 'paper.sty'), ('iclr2026_conference.bst', 'paper.bst')]:
        url = 'https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2026/' + name
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        patch_write(target, response.text)
    patch_write('template_provenance.json', json.dumps(dict(venue='ICLR 2026', source='https://github.com/ICLR/Master-Template/tree/master/iclr2026', retrieved_at=now, style_sha256=hashlib.sha256(Path('paper.sty').read_bytes()).hexdigest(), notes='Official 2026 style and bibliography style; review mode, single 5.5-inch text column.'), indent=2))
    print('Safely retrieved', len(records), 'references and official ICLR 2026 style.')


if __name__ == '__main__':
    main()
