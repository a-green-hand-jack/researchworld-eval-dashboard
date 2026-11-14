import datetime
import json
import re
import time
from pathlib import Path

import requests


SOURCES = [
    ('Aronow2017', 'Estimating average causal effects under general interference, with application to a social network experiment'),
    ('Ugander2013', 'Graph cluster randomization: network exposure to multiple universes'),
    ('Eckles2017', 'Design and analysis of experiments in networks: Reducing bias from interference'),
    ('Chin2019', 'Regression adjustments for estimating the global treatment effect in experiments with interference'),
    ('Han2023', 'Model-based regression adjustment with model-free covariates for network interference'),
    ('Karrer2021', 'Network experimentation at scale'),
    ('Cortez2022', 'Staggered rollout designs enable causal inference under interference without network knowledge'),
    ('Traud2012', 'Social structure of Facebook networks'),
    ('Rossi2015', 'The Network Data Repository with Interactive Graph Analytics and Visualization'),
    ('Choi2012', 'Stochastic blockmodels with a growing number of classes'),
    ('Barabasi1999', 'Emergence of scaling in random networks'),
    ('Watts1998', 'Collective dynamics of small-world networks'),
    ('Hoerl1970', 'Ridge regression: Biased estimation for nonorthogonal problems'),
    ('Golub1979', 'Generalized cross-validation as a method for choosing a good ridge parameter'),
    ('Stein1981', 'Estimation of the mean of a multivariate normal distribution'),
    ('Efron1986', 'How biased is the apparent error rate of a prediction rule?'),
    ('White1980', 'A heteroskedasticity-consistent covariance matrix estimator and a direct test for heteroskedasticity'),
    ('Efron1979', 'Bootstrap methods: Another look at the jackknife'),
    ('Rubin1974', 'Estimating causal effects of treatments in randomized and nonrandomized studies'),
    ('Hudgens2008', 'Toward causal inference with interference'),
    ('Manski2013', 'Identification of treatment response with social interactions'),
    ('Lin2013', 'Agnostic notes on regression adjustments to experimental data: Reexamining Freedman'),
    ('Freedman2008', 'On regression adjustments to experimental data'),
    ('Searle1965', 'Additional results concerning estimable functions and generalized inverse matrices'),
    ('Neyman1990', 'On the application of probability theory to agricultural experiments. Essay on principles. Section 9'),
]


def retrieve():
    destination = Path('reference_evidence')
    destination.mkdir(exist_ok=True)
    fields = 'id,doi,title,publication_year,authorships,abstract_inverted_index,primary_location,biblio'
    references = []
    bibtex = []
    for key, title in SOURCES:
        target = destination / (key + '.json')
        if target.exists():
            record = json.loads(target.read_text())
        else:
            response = requests.get('https://api.openalex.org/works', params={
                'filter': 'title.search:' + title.replace(':', ' ').replace(',', ' '),
                'per-page': 1, 'select': fields}, timeout=45)
            response.raise_for_status()
            matches = response.json()['results']
            if not matches:
                raise RuntimeError('No exact-source candidate for ' + title)
            record = matches[0]
            target.write_text(json.dumps(record, indent=2))
            time.sleep(.2)
        if key == 'Hoerl1970':
            response = requests.get('https://api.openalex.org/works/https://doi.org/10.1080/00401706.1970.10488634',
                params={'select': fields}, timeout=45)
            response.raise_for_status()
            record = response.json()
            target.write_text(json.dumps(record, indent=2))
        crossref_path = destination / (key + '.crossref.json')
        if crossref_path.exists() and key != 'Hoerl1970':
            crossref = json.loads(crossref_path.read_text())
            print_date = crossref.get('published-print', {}).get('date-parts', [])
            if print_date:
                record['publication_year'] = print_date[0][0]
        authors = ' and '.join(author['author']['display_name'] for author in record['authorships'])
        location = record.get('primary_location') or {}
        journal = (location.get('source') or {}).get('display_name') or ''
        title_tex = record['title'].replace('&', r'\&').replace('_', r'\_')
        fields_bib = {'title': '{' + title_tex + '}', 'author': authors,
                      'year': str(record['publication_year'])}
        if journal:
            fields_bib['journal'] = journal.replace('&', r'\&')
        if record.get('doi'):
            fields_bib['doi'] = record['doi'].split('doi.org/')[-1]
        for name, value in (record.get('biblio') or {}).items():
            if value and name in ['volume', 'issue', 'first_page', 'last_page']:
                if name == 'volume':
                    fields_bib['volume'] = str(value)
        bibtex.append('@article{' + key + ',\n' + ',\n'.join(
            '  ' + name + ' = {' + value + '}' for name, value in fields_bib.items()) + '\n}\n')
        inverted = record.get('abstract_inverted_index') or {}
        ordered = sorted((position, word) for word, positions in inverted.items() for position in positions)
        abstract = ' '.join(word for position, word in ordered)
        reading_path = destination / (key + '.txt')
        if abstract or not reading_path.exists():
            reading_path.write_text(record['title'] + '\n\n' + abstract + '\n')
        full_path = destination / (key + '.full.txt')
        scope = 'Title and abstract only; no citation graph or related-content access'
        if full_path.exists():
            reading_path = full_path
            scope = 'Original document abstract and introduction; no citation graph access'
        elif key == 'Watts1998':
            scope = 'Europe PMC abstract; no citation graph or related-content access'
        references.append({'id': 'ref.openalex.' + key, 'paper_id': record['id'],
            'citation_key': key, 'query': title, 'title': record['title'],
            'year': record['publication_year'], 'venue': journal,
            'source_url': record['id'].replace('https://openalex.org/', 'https://api.openalex.org/works/'),
            'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'reading_artifact': str(reading_path),
            'reading_scope': scope,
            'abstract_available': bool(abstract)})
        print(key, record['publication_year'], record['title'], 'abstract words', len(abstract.split()), flush=True)
    Path('references.bib').write_text('\n'.join(bibtex))
    Path('references_provenance.json').write_text(json.dumps({
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'count': len(references), 'queries': [title for key, title in SOURCES],
        'retrieval_note': 'Semantic Scholar direct allowed-source lookup returned HTTP 429; OpenAlex exact-title fallback. Original irrelevant retrieval hits replaced. Read scopes are explicit.',
        'references': references}, indent=2))


if __name__ == '__main__':
    retrieve()
