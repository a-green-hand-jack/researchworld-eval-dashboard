import concurrent.futures
import datetime
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parent
RECORDS = ROOT / 'literature' / 'records'
RECORDS.mkdir(parents=True, exist_ok=True)
SOURCES = [
    ('Muennighoff2023MTEB', 'ARXIV:2210.07316'),
    ('Polo2024Tiny', 'ARXIV:2402.14992'),
    ('Kipnis2024Meta', 'ARXIV:2407.12844'),
    ('Ruan2024Scaling', 'ARXIV:2405.10938'),
    ('Polo2024Sloth', 'ARXIV:2412.06540'),
    ('Tipping1999PPCA', 'DOI:10.1111/1467-9868.00196'),
    ('Rubin1976Missing', 'DOI:10.1093/biomet/63.3.581'),
    ('Dempster1977EM', 'DOI:10.1111/j.2517-6161.1977.tb01600.x'),
    ('Candes2009Completion', 'DOI:10.1007/s10208-009-9045-5'),
    ('Candes2010Noisy', 'DOI:10.1109/JPROC.2009.2035722'),
    ('Keshavan2010Completion', 'DOI:10.1109/TIT.2010.2046205'),
    ('Mazumder2010Spectral', 'DOI:10.1214/10-AOAS364'),
    ('Koren2009Factors', 'DOI:10.1109/MC.2009.263'),
    ('Chaloner1995Design', 'DOI:10.1214/ss/1177009939'),
    ('Lindley1956Information', 'DOI:10.1214/aoms/1177728069'),
    ('Cohn1996Active', 'DOI:10.1613/jair.295'),
    ('Gneiting2011Quantiles', 'DOI:10.1016/j.ijforecast.2009.12.015'),
    ('Koenker1978Quantiles', 'DOI:10.2307/1913643'),
    ('Ghahramani1996Mixture', '09ef86868035bbfd4803a9e1c98640804bf8f4a4'),
    ('Viroli2017Deep', 'fb6cf1fcb62937ea8c16759a7b64191d5abdbcee'),
    ('McNicholas2010Mixture', '69062859b92001292d3bff63e354a708ca00416d'),
    ('Subedi2012Mixture', '694ad2bbb3c55cac461f737ed994fd32082bfe8b'),
    ('Zhao2008ECM', 'db9b835d85361f6250c9ee102279a4fdf6951fdb'),
    ('Viroli2010Mixture', 'deb49c62d806c719cb48324bc7604166325b6cb7'),
    ('Wei2017Missing', 'ae045e3c800e73999080a31bff4dee5dfdfbc152'),
]


def request_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'GroundedPaper/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def fetch_one(specification):
    citation_key, identifier = specification
    target = RECORDS / (citation_key + '.json')
    if target.exists():
        return json.loads(target.read_text())
    encoded = urllib.parse.quote(identifier, safe='')
    url = 'https://api.semanticscholar.org/graph/v1/paper/' + encoded
    url += '?fields=title,authors,year,venue,abstract,externalIds,citationStyles,url,openAccessPdf'
    errors = []
    try:
        data = request_json(url)
        result = {'citation_key': citation_key, 'identifier': identifier,
                  'provider': 'Semantic Scholar', 'source_url': url, 'data': data}
    except Exception as error:
        errors.append(str(error))
        if identifier.startswith('ARXIV:'):
            url = 'https://arxiv.org/abs/' + identifier.split(':')[1]
            with urllib.request.urlopen(url, timeout=60) as response:
                html = response.read().decode()
            soup = BeautifulSoup(html, 'html.parser')
            metadata = {}
            for tag in soup.find_all('meta'):
                metadata.setdefault(tag.get('name'), []).append(tag.get('content'))
            abstract = soup.find('blockquote', class_='abstract')
            data = {'metadata': metadata, 'abstract': abstract.get_text(' ', strip=True) if abstract else None}
            result = {'citation_key': citation_key, 'identifier': identifier,
                      'provider': 'arXiv original abstract', 'source_url': url, 'data': data}
            result['retrieved_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            target.write_text(json.dumps(result, indent=2) + '\n')
            print('RETRIEVED', citation_key, flush=True)
            return result
        if not identifier.startswith('DOI:'):
            original = json.loads((ROOT / 'references_provenance.json').read_text())
            title = next(record['title'] for record in original['references'] if record['paper_id'] == identifier)
            url = 'https://api.crossref.org/works?rows=1&query.title=' + urllib.parse.quote(title)
            try:
                crossref = request_json(url)['message']['items'][0]
                data = request_json('https://api.openalex.org/works/https://doi.org/' + crossref['DOI'])
                result = {'citation_key': citation_key, 'identifier': identifier,
                          'provider': 'OpenAlex', 'source_url': url, 'data': data,
                          'crossref': crossref, 'expected_title': title}
                result['retrieved_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                target.write_text(json.dumps(result, indent=2) + '\n')
                print('RETRIEVED', citation_key, 'check title', data['title'], flush=True)
                return result
            except Exception as error:
                print('FAILED', citation_key, errors + [str(error)], flush=True)
                return None
        url = 'https://api.openalex.org/works/https://doi.org/' + identifier[4:]
        try:
            data = request_json(url)
            result = {'citation_key': citation_key, 'identifier': identifier,
                      'provider': 'OpenAlex', 'source_url': url, 'data': data}
        except Exception as error:
            print('FAILED', citation_key, errors + [str(error)], flush=True)
            return None
    result['retrieved_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    target.write_text(json.dumps(result, indent=2) + '\n')
    print('RETRIEVED', citation_key, flush=True)
    return result


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        records = list(executor.map(fetch_one, SOURCES))
    print('retrieved', sum(record is not None for record in records), 'of', len(SOURCES))


if __name__ == '__main__':
    main()
