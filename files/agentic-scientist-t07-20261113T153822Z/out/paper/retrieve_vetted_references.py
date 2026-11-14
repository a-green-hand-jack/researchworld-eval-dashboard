import concurrent.futures
import datetime
import json
from pathlib import Path

import requests

TARGETS = [
    ('Vivek2024', '10.48550/arXiv.2309.08638'),
    ('Polo2024', '10.48550/arXiv.2402.14992'),
    ('Kipnis2025', '10.48550/arXiv.2407.12844'),
    ('Pacchiardi2024', '10.48550/arXiv.2409.03563'),
    ('Li2025', '10.48550/arXiv.2410.05952'),
    ('Liang2023', '10.48550/arXiv.2211.09110'),
    ('Wang2024', '10.48550/arXiv.2406.01574'),
    ('Hoerl1970', '10.1080/00401706.1970.10488634'),
    ('Elfving1952', '10.1214/aoms/1177729442'),
    ('Kiefer1960', '10.4153/CJM-1960-030-4'),
    ('Andersen1970', '10.1111/j.2517-6161.1970.tb00842.x'),
    ('Dempster1977', '10.1111/j.2517-6161.1977.tb01600.x'),
    ('Hastie2009', '10.1007/978-0-387-84858-7'),
    ('Bishop2006', '10.1007/978-0-387-45528-0'),
    ('Efron1979', '10.1214/aos/1176344552'),
    ('Rubin1976', '10.1093/biomet/63.3.581'),
    ('Little2019', '10.1002/9781119013563'),
    ('Roberts2017', '10.1111/ecog.02881'),
    ('Varma2006', '10.1186/1471-2105-7-91'),
    ('Arlot2010', '10.1214/09-SS054'),
    ('Stone1974', '10.1111/j.2517-6161.1974.tb00994.x'),
    ('Kendall1938', '10.1093/biomet/30.1-2.81'),
    ('Spearman1904', '10.2307/1412159'),
    ('BenDavid2010', '10.1007/s10994-009-5152-4'),
    ('Brier1950', '10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2'),
]


def fetch(target):
    key, doi = target
    url = 'https://api.openalex.org/works/https://doi.org/' + doi
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    work = response.json()
    index = work.get('abstract_inverted_index') or {}
    positions = {position: word for word, locations in index.items() for position in locations}
    abstract = ' '.join(positions[position] for position in sorted(positions))
    authors = ' and '.join(author['author']['display_name'] for author in work['authorships'])
    title = work['title'].replace('&', r'\&')
    venue = ((work.get('primary_location') or {}).get('source') or {}).get('display_name') or 'Preprint'
    bib = f'@misc{{{key},\n title = {{{title}}},\n author = {{{authors}}},\n year = {{{work["publication_year"]}}},\n howpublished = {{{venue}}},\n doi = {{{doi}}}\n}}\n'
    record = dict(id='ref.openalex.' + work['id'].split('/')[-1], paper_id=work['id'], citation_key=key,
                  title=work['title'], year=work['publication_year'], venue=venue, query='Exact DOI: ' + doi,
                  source_url=url, retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  abstract=abstract, doi=doi, consulted_scope='OpenAlex title, metadata and abstract where available; no citation links traversed')
    return bib, record


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch, TARGETS))
    Path('references.bib').write_text('\n'.join(result[0] for result in results))
    Path('references_provenance.json').write_text(json.dumps(dict(
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), count=len(results),
        queries=['Exact DOI: ' + doi for _, doi in TARGETS], references=[result[1] for result in results],
        retrieval_note='Semantic Scholar exact-ID requests returned HTTP 429. OpenAlex exact-DOI fallback. Replaces unrelated supplied retrieval hits; no broad search or citation traversal.'), indent=2))
    Path('reference_consultation.md').write_text('\n\n'.join(
        f'## {record["citation_key"]}: {record["title"]}\n{record["source_url"]}\n\n{record["abstract"] or "No abstract returned. Metadata only; use only for bibliographic context."}'
        for _, record in results))


if __name__ == '__main__':
    main()
