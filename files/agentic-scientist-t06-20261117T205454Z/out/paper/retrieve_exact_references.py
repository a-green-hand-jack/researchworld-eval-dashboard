import concurrent.futures
import datetime
import html
import json
import re
import time
import urllib.request
from pathlib import Path


DOIS = {
    'Bradley1952': '10.2307/2334029',
    'Ford1957': '10.1080/00029890.1957.11989117',
    'Zermelo1929': '10.1007/BF01180541',
    'Thurstone1927': '10.1037/h0070288',
    'Davidson1970': '10.1080/01621459.1970.10481082',
    'Hunter2004': '10.1214/aos/1079120141',
    'Firth1993': '10.1093/biomet/80.1.27',
    'Turner2012': '10.18637/jss.v048.i09',
    'Plackett1975': '10.2307/2346567',
    'Kendall1938': '10.1093/biomet/30.1-2.81',
    'Efron1979': '10.1214/aos/1176344552',
    'Rubin1981': '10.1214/aos/1176345338',
    'Davison1997': '10.1017/CBO9780511802843',
    'Field2007': '10.1111/j.1467-9868.2007.00593.x',
    'Owen2007': '10.1214/07-AOAS122',
    'Hampel1974': '10.1080/01621459.1974.10482962',
    'Cook1977': '10.1080/00401706.1977.10489493',
}
ARXIV = {
    'Koh2017': '1703.04730',
    'Broderick2020': '2011.14999',
    'Chiang2024': '2403.04132',
    'Min2025': '2501.17858',
    'Giordano2019': '1806.00550',
    'Shah2017': '1512.08949',
    'Negahban2012': '1209.1688',
}


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'GroundedResearch/1.0'})
    for delay in (0, 2, 5):
        time.sleep(delay)
        try:
            return urllib.request.urlopen(request, timeout=40).read().decode()
        except Exception:
            if delay == 5:
                raise


def plain(text):
    return html.unescape(re.sub('<[^>]+>', ' ', text)).strip()


def resolve(item):
    key, identity = item
    if key in DOIS:
        url = 'https://api.crossref.org/works/' + identity
        data = json.loads(get(url))['message']
        record = {field: data.get(field) for field in
                  ('DOI', 'title', 'author', 'container-title', 'published', 'volume', 'issue', 'page', 'abstract', 'type', 'publisher', 'URL')}
        record['citation_key'] = key
        record['source_url'] = url
    else:
        url = 'https://arxiv.org/abs/' + identity
        page = get(url)
        def meta(name):
            return re.findall(r'<meta\s+name="' + name + r'"\s+content="([^"]+)"', page)
        abstract = re.search(r'<blockquote class="abstract[^>]*>(.*?)</blockquote>', page, re.S)
        record = {'citation_key': key, 'arxiv': identity, 'title': meta('citation_title'),
                  'author': [{'name': html.unescape(name)} for name in meta('citation_author')],
                  'year': int(meta('citation_date')[0][:4]), 'abstract': plain(abstract.group(1)) if abstract else '',
                  'source_url': url}
    Path('literature', key + '.json').write_text(json.dumps(record, indent=2))
    return key, record


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for key, record in pool.map(resolve, list(DOIS.items()) + list(ARXIV.items())):
            print(key, record['title'], plain(record.get('abstract') or '')[:1700], flush=True)
    documentation = get('https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/README.md')
    Path('literature/NBAdata.md').write_text(documentation)
