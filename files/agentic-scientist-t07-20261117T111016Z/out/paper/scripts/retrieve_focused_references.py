"""Direct identifier retrieval, without search or citation-network expansion."""

import concurrent.futures
import datetime
import html
import json
import re
import time
import urllib.request
from pathlib import Path


ARXIV = {
    'Vivek2024': '2309.08638', 'Polo2024': '2402.14992',
    'Kipnis2025': '2407.12844', 'Pacchiardi2024': '2409.03563',
    'Li2025': '2410.05952', 'Balkir2026': '2601.13885',
    'Wang2024': '2406.01574', 'Liang2023': '2211.09110',
    'Ghosh2024': '2412.06745', 'Suzgun2022': '2210.09261',
    'Rein2023': '2311.12022', 'Sprague2023': '2310.16049',
    'Hendrycks2021': '2103.03874', 'Jin2020': '2009.13081',
    'Hendrycks2020': '2009.03300', 'Guha2023': '2308.11462',
    'Dwork2015': '1506.02629', 'Harris2020': '2006.10256',
    'Virtanen2020': '1907.10121',
}
DOIS = {
    'Hoerl1970': '10.1080/00401706.1970.10488634',
    'Elfving1952': '10.1214/aoms/1177729442',
    'Efron1979': '10.1214/aos/1176344552',
    'Efron1987': '10.1080/01621459.1987.10478410',
    'Hunter2007': '10.1109/MCSE.2007.55',
}
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'literature_evidence'


def fetch(url):
    for retry in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Scientific manuscript bibliography verification/1.0'})
            return urllib.request.urlopen(request, timeout=60).read().decode('utf-8')
        except Exception:
            if retry == 2:
                raise
            time.sleep(2 + retry)


def plain(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', value))).strip()


def bib_text(value):
    return re.sub(r'([&%_#])', r'\\\1', html.unescape(value)).replace('Programming', r'\mbox{Programming}')


def retrieve_arxiv(item):
    key, identifier = item
    url = 'https://arxiv.org/abs/' + identifier
    path = CACHE / (key + '.html')
    if not path.exists():
        path.write_text(fetch(url))
    content = path.read_text()
    meta = re.findall(r'<meta\s+name="([^"]+)"\s+content="([^"]*)"', content)
    metadata = {}
    for name, value in meta:
        metadata.setdefault(name, []).append(html.unescape(value))
    title = metadata['citation_title'][0]
    authors = metadata['citation_author']
    year = int(metadata['citation_date'][0][:4])
    abstract = re.search(r'<blockquote class="abstract[^\"]*"[^>]*>(.*?)</blockquote>', content, re.S)
    record = dict(id='ref.arxiv.' + identifier, paper_id='arXiv:' + identifier,
                  citation_key=key, title=title, authors=authors, year=year,
                  source_url=url, query='Direct supplied or foundational identifier: ' + identifier,
                  abstract=plain(abstract.group(1)) if abstract else '',
                  consulted_path=str(path.relative_to(ROOT)), consultation_scope='abstract and bibliographic metadata')
    record['bibtex'] = '@article{' + key + ',\n  title={{' + bib_text(title) + '}},\n  author={' + ' and '.join(bib_text(author) for author in authors) + '},\n  year={' + str(year) + '},\n  journal={arXiv preprint arXiv:' + identifier + '},\n  url={' + url + '}\n}\n'
    return record


def retrieve_doi(item):
    key, identifier = item
    url = 'https://api.crossref.org/works/' + identifier
    path = CACHE / (key + '.json')
    if not path.exists():
        path.write_text(fetch(url))
    metadata = json.loads(path.read_text())['message']
    authors = [author.get('given', '') + ' ' + author['family'] for author in metadata['author']]
    title = metadata['title'][0]
    year = metadata['published']['date-parts'][0][0]
    venue = plain(metadata['container-title'][0])
    abstract = plain(metadata.get('abstract', ''))
    abstract_source = url
    if not abstract:
        openalex_url = 'https://api.openalex.org/works/https://doi.org/' + identifier
        openalex_path = CACHE / (key + '_openalex.json')
        if not openalex_path.exists():
            openalex_path.write_text(fetch(openalex_url))
        index = json.loads(openalex_path.read_text()).get('abstract_inverted_index') or {}
        words = {position: word for word, positions in index.items() for position in positions}
        abstract = ' '.join(words[position] for position in sorted(words))
        abstract_source = openalex_url
    record = dict(id='ref.doi.' + identifier, paper_id=identifier,
                  citation_key=key, title=title, authors=authors, year=year, venue=venue,
                  source_url=url, query='Direct foundational DOI: ' + identifier,
                  abstract=abstract, abstract_source=abstract_source,
                  consulted_path=str((openalex_path if abstract_source != url else path).relative_to(ROOT)),
                  metadata_path=str(path.relative_to(ROOT)),
                  consultation_scope='Crossref bibliographic metadata and substantive abstract; direct OpenAlex DOI abstract fallback when publisher abstract absent')
    record['bibtex'] = '@article{' + key + ',\n  title={{' + bib_text(title) + '}},\n  author={' + ' and '.join(bib_text(author) for author in authors) + '},\n  year={' + str(year) + '},\n  journal={' + bib_text(venue) + '},\n  doi={' + identifier + '}\n}\n'
    return record


def main():
    CACHE.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(retrieve_arxiv, ARXIV.items()))
        records += list(pool.map(retrieve_doi, DOIS.items()))
    url = 'https://www.jmlr.org/papers/v11/cawley10a.html'
    path = CACHE / 'Cawley2010.html'
    if not path.exists():
        path.write_text(fetch(url))
    text = plain(path.read_text())
    records.append(dict(id='ref.jmlr.cawley10a', paper_id='jmlr:11/cawley10a',
                        citation_key='Cawley2010', title='On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation',
                        authors=['Gavin C. Cawley', 'Nicola L. C. Talbot'], year=2010,
                        venue='Journal of Machine Learning Research', source_url=url,
                        query='Direct known foundational article', abstract=text,
                        consulted_path=str(path.relative_to(ROOT)), consultation_scope='publisher article page and abstract',
                        bibtex='@article{Cawley2010, title={{On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation}}, author={Gavin C. Cawley and Nicola L. C. Talbot}, year={2010}, journal={Journal of Machine Learning Research}, volume={11}, pages={2079--2107}}\n'))
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for record in records:
        record['retrieved_at'] = timestamp
    (ROOT / 'references.bib').write_text('\n'.join(record.pop('bibtex') for record in records))
    provenance = dict(generated_at=timestamp, count=len(records),
                      queries=[record['query'] for record in records], references=records,
                      retrieval_policy='Direct identifiers only; no citation networks, search results, or prohibited-study identity queries. Replaces off-topic preliminary retrieval.')
    (ROOT / 'references_provenance.json').write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + '\n')
    inputs = list(dict.fromkeys([record['consulted_path'] for record in records] +
                               [record.get('metadata_path', record['consulted_path']) for record in records]))
    for output in ['references.bib', 'references_provenance.json']:
        sidecar = dict(schema_name='scientific-evidence.artifact-manifest',
                       artifact=dict(path=output, kind='derived'),
                       derived_from=['@' + 'evidence' + '[' * 2 + target + ']' * 2 for target in inputs],
                       generated_by=dict(script_path='scripts/retrieve_focused_references.py'))
        (ROOT / (output + '.prov.json')).write_text(json.dumps(sidecar, indent=2) + '\n')
    for record in records:
        print(record['citation_key'], record['year'], record['title'], '\n', record['abstract'][:1600], '\n', flush=True)


if __name__ == '__main__':
    main()
