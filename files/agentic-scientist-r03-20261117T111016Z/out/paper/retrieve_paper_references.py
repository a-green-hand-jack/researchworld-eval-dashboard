import datetime
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request


SPECS = [
    ('MTEB', 'ARXIV:2210.07316'),
    ('TinyBenchmarks', 'ARXIV:2402.14992'),
    ('MetaBench', 'ARXIV:2407.12844'),
    ('ObservationalScaling', 'ARXIV:2405.10938'),
    ('Sloth', 'ARXIV:2412.06540'),
    ('Koren2009', 'DOI:10.1109/MC.2009.263'),
    ('Hu2008', 'DOI:10.1109/ICDM.2008.22'),
    ('Candes2009', 'DOI:10.1007/s10208-009-9045-5'),
    ('Jain2013', 'ARXIV:1212.0467'),
    ('Rennie2005', 'DOI:10.1145/1102351.1102441'),
    ('Koenker2001', 'DOI:10.1257/jep.15.4.143'),
    ('Stone1977', 'DOI:10.1214/aos/1176343886'),
    ('Bengio2004', 'No Unbiased Estimator of the Variance of K-Fold Cross-Validation'),
    ('Hoerl1970', 'DOI:10.1080/00401706.1970.10488634'),
    ('Chaloner1995', 'DOI:10.1214/ss/1177009939'),
    ('Cohn1996', 'DOI:10.1613/jair.295'),
    ('Rubin1976', 'DOI:10.1093/biomet/63.3.581'),
    ('Efron1979', 'DOI:10.1214/aos/1176344552'),
    ('Cameron2008', 'DOI:10.1162/rest.90.3.414'),
    ('Takacs2008', 'Matrix factorization and neighbor based algorithms for the netflix prize problem'),
    ('Mnih2007', 'Probabilistic Matrix Factorization'),
    ('Salakhutdinov2008', 'Bayesian Probabilistic Matrix Factorization using Markov Chain Monte Carlo'),
    ('Cover1967', 'DOI:10.1109/TIT.1967.1053964'),
    ('Harris2020', 'DOI:10.1038/s41586-020-2649-2'),
    ('Hunter2007', 'DOI:10.1109/MCSE.2007.55'),
]


def fetch(url):
    for retry in range(4):
        try:
            with urllib.request.urlopen(url, timeout=40) as response:
                return json.load(response)
        except Exception:
            if retry == 3:
                raise
            time.sleep(2 + retry * 3)


def main():
    directory = Path('literature_evidence')
    directory.mkdir(exist_ok=True)
    references = []
    entries = []
    for key, identity in SPECS:
        cache = directory / (key + '.json')
        if cache.exists():
            result = json.loads(cache.read_text())
        else:
            select = 'id,doi,title,publication_year,authorships,abstract_inverted_index,primary_location,biblio,type'
            base = 'https://api.openalex.org/works/'
            if identity.startswith('ARXIV:'):
                identity = 'DOI:10.48550/arXiv.' + identity.split(':')[1]
            if identity.startswith('DOI:'):
                url = base + 'https://doi.org/' + identity[4:] + '?select=' + select
                result = fetch(url)
            else:
                url = base + '?' + urllib.parse.urlencode(dict(search=identity, per_page=1, select=select))
                result = fetch(url)['results'][0]
                canonical = lambda value: ''.join(character.lower() for character in value if character.isalnum())
                assert canonical(result['title']) == canonical(identity), (identity, result['title'])
            result['retrieval_url'] = url
            cache.write_text(json.dumps(result, indent=2))
        escape = lambda value: value.replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')
        names = [author['author']['display_name'] for author in result['authorships']]
        if key == 'Bengio2004':
            names = ['Yoshua Bengio', 'Yves Grandvalet']
        authors = ' and '.join(escape(name) for name in names)
        venue = ((result.get('primary_location') or {}).get('source') or {}).get('display_name', '')
        title = result['title'].replace('Langauge', 'Language')
        entry = '@article{' + key + ',\n author = {' + authors + '},\n title = {{' + escape(title) + '}},\n year = {' + str(result['publication_year']) + '},\n journal = {' + escape(venue) + '},\n doi = {' + (result.get('doi') or '').replace('https://doi.org/', '') + '}\n}'
        entries.append(entry)
        inverted = result.get('abstract_inverted_index') or {}
        positions = {position: word for word, indices in inverted.items() for position in indices}
        abstract = ' '.join(positions[position] for position in sorted(positions))
        reference = dict(id='ref.openalex.' + result['id'].split('/')[-1], paper_id=result['id'], citation_key=key, title=result['title'], normalized_title=title, author_names=names, year=result['publication_year'], venue=venue, query=identity, source_url=result['retrieval_url'], retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), consulted_content='abstract' if abstract else 'metadata only', evidence_path=str(cache))
        if key == 'Bengio2004':
            reference['normalization_note'] = 'Author names corrected against the consulted publisher abstract page.'
            reference['additional_consultation_path'] = 'literature_evidence/Bengio2004_publisher.html'
        if key == 'ObservationalScaling':
            reference['normalization_note'] = 'Title spelling corrected against the explicitly permitted starter title supplied with this task; raw provider metadata retained.'
        references.append(reference)
        print(key, result['title'], '\n', abstract, flush=True)
    assert len({reference['paper_id'] for reference in references}) == len(SPECS)
    Path('references.bib').write_text('\n\n'.join(entries) + '\n')
    Path('references_provenance.json').write_text(json.dumps(dict(generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), count=len(references), queries=[identity for key, identity in SPECS], references=references), indent=2))


if __name__ == '__main__':
    main()
