import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'source_evidence'
SOURCES.mkdir(exist_ok=True)
FILES = {
    'adaptive.py': 'results/ideas/02_cross_fitted_ilr_residual_geometry/program_1/src/program.py',
    'single_split.py': 'results/ideas/01_boundary_stratified_hellinger_reliability_audit/program_1/src/program.py',
    'interpolated.py': 'results/ideas/03_continuous_boundary_covariance_interpolation/program_1/src/program.py',
    'evaluate_final.py': 'task/evaluate_final.py',
    'final_resource_manifest.json': 'task/resources/final/manifest.json',
    'search_resource_manifest.json': 'task/resources/search/manifest.json',
    'requirements.txt': 'task/requirements.txt',
    'adaptive_spec.toml': 'results/ideas/02_cross_fitted_ilr_residual_geometry/program_1/program_spec.toml',
}
manifest = []
for target, original in FILES.items():
    source = ROOT / original
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copyfile(source, SOURCES / target)
    manifest.append({'path': str(Path('source_evidence') / target), 'original': original,
                     'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
(SOURCES / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

REFERENCES = [
    ('Vovk2005', '10.1007/b106715'),
    ('Papadopoulos2002', '10.1007/3-540-36755-1_29'),
    ('Lei2018', '10.1080/01621459.2017.1307116'),
    ('Barber2021Jackknife', '10.1214/20-AOS1965'),
    ('Tibshirani2019', 'arxiv:1904.06019'),
    ('Angelopoulos2021', 'arxiv:2107.07511'),
    ('Aitchison1982', '10.1111/j.2517-6161.1982.tb01195.x'),
    ('Egozcue2003', '10.1023/A:1023818214614'),
    ('AitchisonShen1980', '10.1093/biomet/67.2.261'),
    ('Pawlowsky2011', '10.1002/9781119976462'),
    ('SchaferStrimmer2005', '10.2202/1544-6115.1175'),
    ('Chen2010', '10.1109/TSP.2010.2053029'),
    ('HoerlKennard1970', '10.1080/00401706.1970.10488634'),
    ('Stone1974', '10.1111/j.2517-6161.1974.tb00994.x'),
    ('Geisser1975', '10.1080/01621459.1975.10479865'),
    ('Brown2001', '10.1214/ss/1009213286'),
    ('Efron1979', '10.1214/aos/1176344552'),
    ('Davison1997', '10.1017/CBO9780511802843'),
    ('Romano2019', 'arxiv:1905.03222'),
    ('Barber2021Limits', '10.1093/imaiai/iaaa017'),
    ('Barber2023', '10.1214/23-AOS2276'),
    ('Gneiting2007', '10.1198/016214506000001437'),
    ('Vovk2012', 'arxiv:1209.2673'),
    ('Romano2020', 'arxiv:2006.02544'),
    ('Ding2023', 'arxiv:2306.09335'),
]

def fetch(reference):
    key, identifier = reference
    directory = ROOT / 'literature' / key
    directory.mkdir(parents=True, exist_ok=True)
    if identifier.startswith('arxiv:'):
        number = identifier.split(':')[1]
        url = 'https://arxiv.org/abs/' + number
        request = urllib.request.Request(url, headers={'User-Agent': 'ScientificPaperEvidence/1.0'})
        content = urllib.request.urlopen(request, timeout=60).read()
        (directory / 'abstract.html').write_bytes(content)
        pdf_url = 'https://arxiv.org/pdf/' + number
        try:
            (directory / 'paper.pdf').write_bytes(urllib.request.urlopen(pdf_url, timeout=90).read())
        except Exception as error:
            (directory / 'pdf_failure.txt').write_text(str(error))
        return key, identifier, url, 'arxiv'
    url = 'https://api.crossref.org/works/' + identifier
    request = urllib.request.Request(url, headers={'User-Agent': 'ScientificPaperEvidence/1.0'})
    if (directory / 'metadata.json').exists():
        return key, identifier, url, 'crossref-cached'
    import time
    for retry in range(6):
        try:
            content = urllib.request.urlopen(request, timeout=60).read()
            break
        except Exception:
            if retry == 5:
                raise
            time.sleep(3 * (retry + 1))
    time.sleep(1)
    metadata = json.loads(content)['message']
    (directory / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return key, identifier, url, 'crossref'

if __name__ == '__main__':
    for reference in REFERENCES:
        print(*fetch(reference), flush=True)
