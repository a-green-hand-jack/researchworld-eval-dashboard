import concurrent.futures
import datetime
import json
import re
from pathlib import Path

import requests


RECORDS = [
    ('Glickman1999', '10.1111/1467-9876.00159'),
    ('Thurstone1927', '10.1037/h0070288'),
    ('Zermelo1929', '10.1007/BF01180541'),
    ('Maystre2015', 'openalex:W1948584817'),
    ('Davidson1970', '10.1080/01621459.1970.10481082'),
    ('Rao1967', '10.1080/01621459.1967.10482901'),
    ('Hunter2004', '10.1214/aos/1079120141'),
    ('Turner2012', '10.18637/jss.v048.i09'),
    ('Firth1993', '10.1093/biomet/80.1.27'),
    ('Albert1984', '10.1093/biomet/71.1.1'),
    ('Fagin2003', '10.1137/S0895480102412856'),
    ('Diaconis1977', '10.1111/j.2517-6161.1977.tb01624.x'),
    ('Negahban2017', '10.1287/opre.2016.1534'),
    ('Jiang2011', '10.1007/s10107-010-0419-x'),
    ('Bubeck2015', 'arxiv:1405.4980'),
    ('Hampel1974', '10.1080/01621459.1974.10482962'),
    ('Cook1977', '10.1080/00401706.1977.10489493'),
    ('Efron1979', '10.1214/aos/1176344552'),
    ('Efron1986', '10.1214/ss/1177013815'),
    ('Davison1997', '10.1017/CBO9780511802843'),
    ('Cameron2008', '10.1162/rest.90.3.414'),
    ('Huber1964', '10.1214/aoms/1177703732'),
    ('Koh2017', 'arxiv:1703.04730'),
    ('Broderick2020', 'arxiv:2011.14999'),
    ('Chiang2024', 'arxiv:2403.04132'),
]


def retrieve(record):
    key, identifier = record
    if identifier.startswith('arxiv:'):
        arxiv_id = identifier.split(':')[1]
        url = f'https://arxiv.org/abs/{arxiv_id}'
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        Path(f'literature/{key}.html').write_text(response.text)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = {}
        for item in soup.select('meta[name^="citation_"]'):
            metadata.setdefault(item['name'], []).append(item['content'])
        title = metadata['citation_title'][0]
        authors = metadata['citation_author']
        year = int(metadata['citation_date'][0][:4])
        abstract = soup.select_one('blockquote.abstract').get_text(' ', strip=True)
        payload = {'title': title, 'authors': authors, 'year': year, 'abstract': abstract}
        pdf_url = f'https://arxiv.org/pdf/{arxiv_id}'
        bib = f'@article{{{key},\n title={{{title}}},\n author={{{" and ".join(authors)}}},\n year={{{year}}},\n journal={{arXiv preprint arXiv:{arxiv_id}}},\n url={{{url}}}\n}}\n'
    else:
        url = f'https://api.openalex.org/works/{identifier.split(":", 1)[1]}' if identifier.startswith('openalex:') else f'https://api.openalex.org/works/https://doi.org/{identifier}'
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        payload = response.json()
        title = payload['title']
        year = payload['publication_year']
        authors = [item['author']['display_name'] for item in payload['authorships']]
        inverted = payload.get('abstract_inverted_index') or {}
        words = {position: word for word, positions in inverted.items() for position in positions}
        abstract = ' '.join(words[position] for position in sorted(words))
        pdf_url = (payload.get('best_oa_location') or {}).get('pdf_url')
        crossref = None if identifier.startswith('openalex:') else requests.get(f'https://api.crossref.org/works/{identifier}', timeout=45)
        cross = crossref.json()['message'] if crossref is not None and crossref.ok else {
            'title': [title], 'container-title': [(payload.get('primary_location') or {}).get('source', {}).get('display_name', '')],
            'type': payload.get('type', 'article'),
            **{key: value for key, value in (payload.get('biblio') or {}).items() if value}
        }
        Path(f'literature/{key}.crossref.json').write_text(json.dumps(cross, indent=2))
        if not abstract:
            abstract = re.sub('<[^>]+>', ' ', cross.get('abstract', '')).strip()
        author_names = [f"{item.get('given', '')} {item.get('family', '')}".strip() for item in cross.get('author', [])]
        if author_names:
            authors = author_names
        venue = (cross.get('container-title') or [''])[0]
        entry_type = 'book' if cross.get('type') in ['book', 'monograph'] else 'article'
        title = re.sub('<[^>]+>', '', cross.get('title', [title])[0]).replace('&', '\\&')
        bib = f'@{entry_type}{{{key},\n title={{{title}}},\n author={{{" and ".join(authors)}}},\n year={{{year}}},\n {"publisher" if entry_type == "book" else "journal"}={{{cross.get("publisher", "") if entry_type == "book" else venue}}},\n {"url" if identifier.startswith("openalex:") else "doi"}={{{url if identifier.startswith("openalex:") else identifier}}}'
        for field in ['volume', 'issue', 'page']:
            if field in cross:
                bib += f',\n {dict(issue="number", page="pages").get(field, field)}={{{cross[field]}}}'
        bib += '\n}\n'
    Path(f'literature/{key}.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    Path(f'literature/{key}.reading.txt').write_text(f'{title}\n{abstract}\n')
    if pdf_url:
        try:
            pdf = requests.get(pdf_url, timeout=50)
            if pdf.ok and pdf.content.startswith(b'%PDF'):
                Path(f'literature/{key}.pdf').write_bytes(pdf.content)
        except requests.RequestException:
            pass
    provenance = {'id': f'ref.direct.{key}', 'paper_id': identifier, 'citation_key': key,
                  'title': title, 'year': year, 'query': f'direct identifier {identifier}',
                  'source_url': url, 'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'reading_path': f'literature/{key}.reading.txt', 'abstract_available': bool(abstract)}
    print(key, title, 'abstract', bool(abstract), flush=True)
    return bib, provenance


if __name__ == '__main__':
    previous = json.loads(Path('references_provenance.json').read_text()) if Path('references_provenance.json').exists() else {'references': []}
    previous_refs = {entry['citation_key']: entry for entry in previous['references']}
    previous_bib = {entry.split('{', 1)[1].split(',', 1)[0]: entry for entry in
                    re.findall(r'@\w+\{.*?\n\}', Path('references.bib').read_text(), re.S)} if Path('references.bib').exists() else {}
    results = []
    for key, identifier in RECORDS:
        if key in previous_refs and key in previous_bib and previous_refs[key]['paper_id'] == identifier:
            bib = re.sub('<[^>]+>', '', previous_bib[key])
            results.append((bib, previous_refs[key]))
        else:
            results.append(retrieve((key, identifier)))
    Path('references.bib').write_text('\n'.join(record[0] for record in results))
    Path('references_provenance.json').write_text(json.dumps({
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'count': len(results), 'queries': [f'direct identifier {value}' for _, value in RECORDS],
        'references': [record[1] for record in results],
        'restriction': 'Direct original identifiers only; no citation expansion or protected-study discovery.'
    }, indent=2))
