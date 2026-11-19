import concurrent.futures
import datetime
import html
import json
import pathlib
import re
import urllib.parse
import urllib.request


WORKS = [
    ('PPI', 'Prediction-powered inference', '10.1126/science.adi6000', None),
    ('PPIPlus', 'PPI++: Efficient Prediction-Powered Inference', None, '2311.01453'),
    ('CrossPPI', 'Cross-prediction-powered inference', None, '2309.16598'),
    ('DML', 'Double/debiased machine learning for treatment and structural parameters', '10.1111/ectj.12097', None),
    ('Vaishnav', 'The evolution, evolvability and engineering of gene regulatory DNA', '10.1038/s41586-022-04506-6', None),
    ('ClopperPearson', 'The use of confidence or fiducial limits illustrated in the case of the binomial', '10.1093/biomet/26.4.404', None),
    ('Student', 'The probable error of a mean', '10.1093/biomet/6.1.1', None),
    ('Brown', 'Interval estimation for a binomial proportion', '10.1214/ss/1009213286', None),
    ('Efron', 'Bootstrap methods: Another look at the jackknife', '10.1214/aos/1176344552', None),
    ('EfronTibshirani', 'An Introduction to the Bootstrap', '10.1007/978-1-4899-4541-9', None),
    ('Hoeffding', 'Probability inequalities for sums of bounded random variables', '10.1080/01621459.1963.10500830', None),
    ('MaurerPontil', 'Empirical Bernstein Bounds and Sample Variance Penalization', None, '0907.3740'),
    ('Dunn', 'Multiple comparisons among means', '10.1080/01621459.1961.10482090', None),
    ('Holm', 'A Simple Sequentially Rejective Multiple Test Procedure', '10.2307/4615733', None),
    ('Cassel', 'Some results on generalized difference estimation and generalized regression estimation for finite populations', '10.1093/biomet/63.3.615', None),
    ('Sarndal', 'Model Assisted Survey Sampling', '10.1007/978-1-4612-4378-6', None),
    ('Rubin', 'Empirical efficiency maximization: improved locally efficient covariate adjustment in randomized experiments and survival analysis', '10.2202/1557-4679.1084', None),
    ('Zhang', 'Semi-supervised inference: General theory and estimation of means', '10.1214/18-AOS1756', None),
    ('Glynn', 'Some new perspectives on the method of control variates', None, None),
    ('Hastie', 'The Elements of Statistical Learning', '10.1007/978-0-387-84858-7', None),
    ('Hoerl', 'Ridge regression: Biased estimation for nonorthogonal problems', '10.1080/00401706.1970.10488634', None),
    ('Stone', 'Cross-validatory choice and assessment of statistical predictions', '10.1111/j.2517-6161.1974.tb00994.x', None),
    ('Wolpert', 'Stacked generalization', '10.1016/S0893-6080(05)80023-1', None),
    ('Breiman', 'Stacked regressions', '10.1007/BF00117832', None),
    ('Nadeau', 'Inference for the generalization error', '10.1023/A:1024068626366', None),
]


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'GroundedManuscript/1.0'})
    with urllib.request.urlopen(request, timeout=50) as response:
        return response.read()


def retrieve(item):
    key, title, doi, arxiv = item
    directory = pathlib.Path('reference_evidence')
    if arxiv:
        url = 'https://arxiv.org/abs/' + arxiv
        document = fetch(url).decode()
        (directory / (key + '.html')).write_text(document)
        metadata = {}
        for name, value in re.findall(r'<meta name="(citation_[^"]+)" content="([^"]*)"', document):
            metadata.setdefault(name, []).append(html.unescape(value))
        record = {'id': 'https://arxiv.org/abs/' + arxiv, 'title': metadata['citation_title'][0],
                  'publication_year': int(metadata['citation_date'][0][:4]),
                  'authorships': [{'author': {'display_name': name}} for name in metadata['citation_author']],
                  'abstract_inverted_index': {word: [position] for position, word in enumerate(metadata.get('citation_abstract', [''])[0].split())}}
    elif doi:
        url = 'https://api.openalex.org/works/https://doi.org/' + doi
        record = json.loads(fetch(url))
    else:
        query = title if not arxiv else title + ' ' + arxiv
        url = 'https://api.openalex.org/works?' + urllib.parse.urlencode({'search': query, 'per-page': 1})
        record = json.loads(fetch(url))['results'][0]
    (directory / (key + '.json')).write_text(json.dumps(record, indent=2))
    abstract = record.get('abstract_inverted_index') or {}
    ordered = sorted((position, word) for word, positions in abstract.items() for position in positions)
    text = ' '.join(word for position, word in ordered)
    if arxiv:
        match = re.search(r'<blockquote class="abstract[^>]*>(.*?)</blockquote>', document, re.S)
        if match:
            text = re.sub('<[^>]*>', '', match[1])
    (directory / (key + '.txt')).write_text(record['title'] + '\n' + text + '\n')
    authors = ' and '.join(author['author']['display_name'] for author in record['authorships'])
    venue = ((record.get('primary_location') or {}).get('source') or {}).get('display_name', '')
    protected_title = record['title'].replace('PPI++', '{PPI++}').replace('DNA', '{DNA}').replace('Bernstein', '{Bernstein}')
    fields = {'title': protected_title, 'author': authors, 'year': str(record['publication_year'])}
    if doi:
        fields['doi'] = doi
    if arxiv:
        fields['eprint'] = arxiv
        fields['archivePrefix'] = 'arXiv'
    if arxiv:
        fields['journal'] = 'arXiv preprint arXiv:' + arxiv
    elif venue:
        fields['journal'] = venue
    bib = '@article{' + key + ',\n' + '\n'.join('  '+field+' = {'+value+'},' for field, value in fields.items()) + '\n}\n'
    provenance = dict(id=('ref.arxiv.' if arxiv else 'ref.openalex.')+record['id'].split('/')[-1], paper_id=record['id'], citation_key=key,
                      title=record['title'], year=record['publication_year'], query=title, source_url=url,
                      retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      consulted_file='reference_evidence/'+key+'.txt', consultation_scope='Exact-work metadata and available abstract only; no citation graph followed.')
    print(key, record['publication_year'], record['title'], 'abstract_chars', len(text), flush=True)
    return bib, provenance


def main():
    pathlib.Path('reference_evidence').mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        entries = list(executor.map(retrieve, WORKS))
    pathlib.Path('references.bib').write_text('\n'.join(bib for bib, provenance in entries))
    pathlib.Path('references_provenance.json').write_text(json.dumps(dict(
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), count=len(entries),
        queries=[item[1] for item in WORKS], references=[provenance for bib, provenance in entries]), indent=2))


if __name__ == '__main__':
    main()
