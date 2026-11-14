import concurrent.futures
import json
import pathlib
import subprocess
import urllib.request
from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parent
URLS = {
    'Ghahramani1996Mixture': 'https://www.cs.toronto.edu/~hinton/absps/factor.pdf',
    'Gneiting2011Quantiles': 'https://www.stat.washington.edu/raftery/Research/PDF/Gneiting2011.pdf',
    'Chaloner1995Design': 'https://projecteuclid.org/journals/statistical-science/volume-10/issue-3/Bayesian-Experimental-Design-A-Review/10.1214/ss/1177009939.full',
    'Lindley1956Information': 'https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-27/issue-4/On-a-Measure-of-the-Information-Provided-by-an-Experiment/10.1214/aoms/1177728069.full',
    'Keshavan2010Completion': 'https://arxiv.org/abs/0901.3150',
    'Viroli2017Deep': 'https://arxiv.org/abs/1711.06929',
    'Viroli2010Mixture': 'https://link.springer.com/article/10.1007/s00357-010-9063-7',
    'McNicholas2010Mixture': 'https://doi.org/10.1016/j.jspi.2009.11.006',
    'Koren2009Factors': 'https://www.cs.rochester.edu/twiki/pub/Main/HarpSeminar/MatrixFactorization.pdf',
    'Koenker1978Quantiles': 'https://www.econ.uiuc.edu/~roger/research/rq/rq.pdf',
}


def fetch_one(item):
    key, url = item
    path = ROOT / 'literature/records' / (key + '.json')
    record = json.loads(path.read_text())
    if record.get('original_excerpt'):
        return
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=50) as response:
            data = response.read()
        if data.startswith(b'%PDF'):
            pdf = ROOT / 'literature' / (key + '.pdf')
            pdf.write_bytes(data)
            text = subprocess.check_output(['pdftotext', str(pdf), '-']).decode()
            record['original_excerpt'] = text[:14000]
        else:
            soup = BeautifulSoup(data.decode(), 'html.parser')
            title = soup.title.get_text() if soup.title else ''
            abstracts = soup.find_all('blockquote', class_='abstract') or soup.find_all('div', class_='abstract')
            record['original_excerpt'] = title + '\n' + '\n'.join(element.get_text(' ', strip=True) for element in abstracts)
            if not abstracts:
                record['original_excerpt'] = soup.get_text(' ', strip=True)[:16000]
        record['original_url'] = url
        path.write_text(json.dumps(record, indent=2) + '\n')
        print('READ', key, record['original_excerpt'][:180].replace('\n', ' '), flush=True)
    except Exception as error:
        print('FAILED', key, str(error), flush=True)


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(fetch_one, URLS.items()))
