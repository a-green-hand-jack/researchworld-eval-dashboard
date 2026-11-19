"""Safe output-capture compatibility and reproducible public-data acquisition.

Importing this module performs no capture, I/O or network access. To recapture:
python capture.py --source_dir /tmp/public-source --output_root /tmp/new-resources
The source directory must contain german.zip, ca.zip, ny.zip, acs.py,
folktables-LICENSE, census-site-policy.html, census-terms.html,
dictionary2024.pdf and relshipp2024.json obtained from
exact URLs recorded in each frozen provenance.json. Acquisition is drafting-only.
"""
import contextlib
import csv
import decimal
import gzip
import hashlib
import io
import json
from pathlib import Path
import unicodedata
import zipfile


class OutputCapture:
    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self._stack = None

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self.stdout))
        self._stack.enter_context(contextlib.redirect_stderr(self.stderr))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._stack.__exit__(exc_type, exc_value, traceback)

    def get_output(self):
        return self.stdout.getvalue(), self.stderr.getvalue()


def encode(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':'),sort_keys=True).encode('utf-8')


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def number(value):
    if value is None or not str(value).strip():
        return None
    numeric = decimal.Decimal(str(value).strip())
    if not numeric.is_finite():
        return None
    return '0' if numeric == 0 else format(numeric.normalize(),'f')


def normalize(row, numeric):
    return [None if value is None or not str(value).strip() else
            ['number',number(value)] if index in numeric else
            ['text',' '.join(unicodedata.normalize('NFKC',str(value)).split())]
            for index,value in enumerate(row)]


def partition(groups, salt, limit=None):
    ordered = sorted(groups,key=lambda item:hashlib.sha256((salt+item['content_sha256']).encode()).digest())
    if limit is not None:
        ordered = ordered[:limit]
    count = len(ordered)
    for index,record in enumerate(ordered):
        record['role'] = 'train' if index < int(.6*count) else 'validation' if index < int(.8*count) else 'explanation'
    return ordered


def acquire(source, output):
    numeric_german = {1,4,7,10,12,15,17}
    with zipfile.ZipFile(source/'german.zip') as archive:
        rows = archive.read('german.data').decode().splitlines()
    grouped = {}
    for index,line in enumerate(rows):
        tokens = line.split()
        normalized = normalize(tokens[:-1],numeric_german)
        content = digest(normalized)
        provenance = {'row':index+1,'source_id':f'uci144:{index+1}','full_record_sha256':digest(tokens)}
        if content not in grouped:
            grouped[content] = {'raw':tokens[:-1],'y':int(tokens[-1]) == 2,'content_sha256':content,'provenance':[],'conflicting_labels':False}
        record = grouped[content]
        record['conflicting_labels'] |= record['y'] != (int(tokens[-1]) == 2)
        record['provenance'].append(provenance)
    all_german = sorted(grouped.values(),key=lambda item:hashlib.sha256(('german-plane-2026'+item['content_sha256']).encode()).digest())
    midpoint = len(all_german)//2
    german = {'search':partition(all_german[:midpoint],'german-within-2026'),
              'final':partition(all_german[midpoint:],'german-within-2026')}
    features = ['AGEP','COW','SCHL','MAR','OCCP','POBP','RELSHIPP','WKHP','SEX','RAC1P']
    populations = {}
    raw_hashes = {}
    stats = {}
    for plane,state in [('search','ca'),('final','ny')]:
        groups = {}
        seen = set()
        total = 0
        included = 0
        with zipfile.ZipFile(source/f'{state}.zip') as archive:
            members = sorted(name for name in archive.namelist() if name.lower().endswith('.csv'))
            for member in members:
                with archive.open(member) as stream:
                    reader = csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig',newline=''))
                    for index,row in enumerate(reader):
                        total += 1
                        raw = [row[name] for name in features]
                        content = digest(normalize(raw,set(range(10))))
                        seen.add(content)
                        allowed = all(number(row[key]) is not None for key in ['AGEP','PINCP','WKHP','PWGTP']) and decimal.Decimal(row['AGEP']) > 16 and decimal.Decimal(row['PINCP']) > 100 and decimal.Decimal(row['WKHP']) > 0 and decimal.Decimal(row['PWGTP']) >= 1
                        if not allowed:
                            continue
                        included += 1
                        label = decimal.Decimal(row['PINCP']) > 50000
                        if content not in groups:
                            groups[content] = {'raw':raw,'y':label,'content_sha256':content,'provenance':[],'conflicting_labels':False}
                        record = groups[content]
                        record['conflicting_labels'] |= record['y'] != label
                        record['provenance'].append({'row':index+1,'member':member,'source_id':f'{row["SERIALNO"]}:{row["SPORDER"]}',
                                                     'population_filter':True,'full_record_sha256':digest(row)})
        populations[plane] = groups
        raw_hashes[plane] = seen
        stats[plane] = {'raw_records':total,'population_records':included,'unique_population_predictors':len(groups)}
    overlap = raw_hashes['search'] & raw_hashes['final']
    for plane in ('search','final'):
        groups = [record for content,record in populations[plane].items() if content not in overlap]
        populations[plane] = partition(groups,'acs-within-2026',33334)
    all_search = {record['content_sha256'] for record in german['search']+populations['search']}
    all_final = {record['content_sha256'] for record in german['final']+populations['final']}
    if all_search & all_final:
        raise ValueError('normalized predictor overlap')
    metadata = {
        'normalization':'Before population filtering, splitting or preprocessing: fixed original predictor order; numeric Decimal canonical finite decimal strings, all zeros canonical 0; categorical Unicode NFKC with split/join whitespace; null sentinel; typed canonical sorted compact UTF-8 JSON. IDs, labels and provenance excluded from content hash. Full records separately hashed.',
        'split':'Deterministic SHA256 ordering salts german-plane-2026, german-within-2026, acs-within-2026. German content groups 50:50 planes, then 60:20:20; ACS excludes ALL CA/NY raw predictor overlaps before selection of 33334 content groups/state and 60:20:20. One representative/group, duplicate and conflicting-label provenance retained.',
        'excluded_cross_state_raw_content_groups':len(overlap),
        'cross_plane_retained_content_intersection':0,
        'folktables_revision':'ebace19d8065efc43589f0067bf183398eb156b9',
        'explicit_2024_schema_adapter':'The supplied folktables commit names RELP, absent from actual 2024 CA/NY releases. Use native RELSHIPP as the original relationship feature group, without fabricating an old-code crosswalk. Keep the other nine predictors, official adult filter and PINCP>50000 target unchanged. Report this as ACSIncome-2024-RELSHIPP, not bit-identical old ACSIncome.',
        'sources':[
            {'file':'german.zip','url':'https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip','license':'CC BY 4.0; UCI DOI 10.24432/C5NC77'},
            {'file':'ca.zip','url':'https://www2.census.gov/programs-surveys/acs/data/pums/2024/1-Year/csv_pca.zip','last_modified':'2025-12-04T12:00:07Z','license':'US government public data; Census copyright terms archived'},
            {'file':'ny.zip','url':'https://www2.census.gov/programs-surveys/acs/data/pums/2024/1-Year/csv_pny.zip','last_modified':'2025-12-04T12:00:09Z','license':'US government public data; no separate SPDX license assigned'},
            {'file':'acs.py','url':'https://raw.githubusercontent.com/socialfoundations/folktables/ebace19d8065efc43589f0067bf183398eb156b9/folktables/acs.py','license':'MIT'},
            {'file':'folktables-LICENSE','url':'https://raw.githubusercontent.com/socialfoundations/folktables/ebace19d8065efc43589f0067bf183398eb156b9/LICENSE.txt','license':'MIT'},
            {'file':'census-site-policy.html','url':'https://www.census.gov/about/policies/privacy.html','license':'Census site policy, no separate SPDX license assigned'},
            {'file':'census-terms.html','url':'https://www.census.gov/about/policies/privacy/privacy-policy.html','license':'Census privacy policy, no separate SPDX license assigned'},
            {'file':'dictionary2024.pdf','url':'https://www2.census.gov/programs-surveys/acs/tech_docs/pums/data_dict/PUMS_Data_Dictionary_2024.pdf','license':'US government technical documentation'},
            {'file':'relshipp2024.json','url':'https://api.census.gov/data/2024/acs/acs1/pums/variables/RELSHIPP.json','license':'US government variable metadata'}],
        'limitations':['Raw release archives retained by URL and digest, not duplicated in runtime. Frozen selected raw predictor records suffice for offline evaluation. Official conference template, independent source review, full statistical inference and paper remain downstream obligations. No prohibited literature was queried.']}
    for item in metadata['sources']:
        item['sha256'] = hashlib.sha256((source/item['file']).read_bytes()).hexdigest()
    for plane in ('search','final'):
        root = output/plane
        root.mkdir(parents=True,exist_ok=True)
        for name,records,numeric in [('german',german[plane],numeric_german),('acs',populations[plane],set(range(10)))]:
            payload = {'name':name,'features':features if name=='acs' else [f'attribute_{index+1}' for index in range(20)],'numeric':sorted(numeric),'records':records}
            with (root/f'{name}.json.gz').open('wb') as stream:
                with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as compressed:
                    compressed.write(encode(payload))
        provenance = dict(metadata)
        provenance['population_counts'] = stats[plane]
        provenance['retained_counts'] = {'german':len(german[plane]),'acs':len(populations[plane])}
        provenance['local_content_audit_sha256'] = digest(sorted(record['content_sha256'] for record in german[plane]+populations[plane]))
        (root/'provenance.json').write_bytes(encode(provenance)+b'\n')
        for filename in ['acs.py','folktables-LICENSE','census-site-policy.html','census-terms.html','dictionary2024.pdf','relshipp2024.json']:
            (root/filename).write_bytes((source/filename).read_bytes())
    print(json.dumps({'retained':{plane:{'german':len(german[plane]),'acs':len(populations[plane])} for plane in ('search','final')},'excluded_overlap_groups':len(overlap)}))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_dir',required=True,type=Path)
    parser.add_argument('--output_root',required=True,type=Path)
    arguments = parser.parse_args()
    acquire(arguments.source_dir,arguments.output_root)
