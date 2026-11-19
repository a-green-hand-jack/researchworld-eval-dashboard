import datetime
import json
import pathlib
import re
import unicodedata
import urllib.request

from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parent
RECORDS = ROOT / 'literature/records'


def original_arxiv(key, identifier):
    path = RECORDS / (key + '.json')
    if path.exists():
        return
    url = 'https://arxiv.org/abs/' + identifier
    with urllib.request.urlopen(url, timeout=40) as response:
        soup = BeautifulSoup(response.read(), 'html.parser')
    metadata = {}
    for tag in soup.find_all('meta'):
        metadata.setdefault(tag.get('name'), []).append(tag.get('content'))
    path.write_text(json.dumps({'citation_key': key, 'identifier': 'ARXIV:' + identifier,
                               'provider': 'arXiv original abstract', 'source_url': url,
                               'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                               'data': {'metadata': metadata, 'abstract': soup.find('blockquote', class_='abstract').get_text(' ', strip=True)}}, indent=2) + '\n')


def latex(value):
    replacements = {'ł': r'{\l}', 'Ł': r'{\L}', 'ø': r'{\o}', 'Ø': r'{\O}',
                    'ß': r'{\ss}', 'æ': r'{\ae}', 'Æ': r'{\AE}', '&': r'\&', '%': r'\%', '_': r'\_'}
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def main():
    original_arxiv('Hendrycks2021MMLU', '2009.03300')
    original_arxiv('Liang2023HELM', '2211.09110')
    original_arxiv('Gneiting2011Forecasts', '0912.0902')
    skip = {'Lindley1956Information', 'McNicholas2010Mixture', 'Gneiting2011Quantiles'}
    records = []
    bibtex = []
    notes = ['# Literature consultation and safety log', '',
             'Only exact, explicitly permitted starter titles or older statistical/methodological works were retrieved. No broad benchmark-prediction discovery, citation expansion, prohibited-paper identification, or prohibited content was used. Original abstracts and the excerpts below were consulted; no claim of full-text reading is made for abstract-only sources.', '',
             'Rejected records: a supplied DOI proposed for the spectral-regularization article resolved to an unrelated biomedical article; it was discarded and replaced by the verified JMLR original. An arXiv lookup for a quantile-forecasting article resolved instead to Making and Evaluating Point Forecasts; the distinct, verified article is cited under its own title. An unrelated mechanical-device abstract attached to the EM article was discarded in favor of the publisher abstract. Blocked/redirect-only publisher responses were not treated as reading. Unread metadata-only references were removed. No prohibited content was encountered.', '']
    for path in sorted(RECORDS.glob('*.json')):
        if path.stem in skip:
            continue
        record = json.loads(path.read_text())
        key = record['citation_key']
        if key == 'Koenker1978Quantiles':
            key = 'Koenker2001Quantiles'
        data = record['data']
        crossref = record.get('crossref', {})
        metadata = data.get('metadata', {})
        arxiv = record['provider'] == 'arXiv original abstract'
        if arxiv:
            title = metadata['citation_title'][0]
            authors = metadata['citation_author']
            year = int(metadata['citation_date'][0][:4])
            venue = 'arXiv preprint arXiv:' + record['identifier'].split(':', 1)[1]
        elif record['provider'] == 'JMLR original':
            title = 'Spectral Regularization Algorithms for Learning Large Incomplete Matrices'
            authors = ['Rahul Mazumder', 'Trevor Hastie', 'Robert Tibshirani']
            year = 2010
            venue = 'Journal of Machine Learning Research'
        else:
            title = crossref.get('title', [data.get('title', '')])[0]
            authors = [((author.get('given', '') + ' ' + author.get('family', '')).strip()) for author in crossref.get('author', [])]
            if not authors:
                authors = [author.get('name') or author.get('author', {}).get('display_name') for author in data.get('authors', data.get('authorships', []))]
            print_date = crossref.get('published-print', {}).get('date-parts')
            year = print_date[0][0] if print_date else (data.get('year') or data.get('publication_year'))
            if not year:
                date = crossref.get('published', crossref.get('issued', {}))
                year = date['date-parts'][0][0]
            location_source = (data.get('primary_location') or {}).get('source') or {}
            venue = (crossref.get('container-title') or [data.get('venue') or location_source.get('display_name') or 'Technical report'])[0]
            if record['identifier'].startswith('ARXIV:'):
                venue = 'arXiv preprint arXiv:' + record['identifier'].split(':', 1)[1]
        abstract = record.get('read_abstract') or data.get('abstract')
        if not abstract and data.get('abstract_inverted_index'):
            words = {position: word for word, positions in data['abstract_inverted_index'].items() for position in positions}
            abstract = ' '.join(words[position] for position in sorted(words))
        excerpt = record.get('original_excerpt', '')
        if key == 'Ghahramani1996Mixture':
            import pymupdf
            excerpt = ''.join(page.get_text() for page in pymupdf.open(ROOT / 'literature/Ghahramani1996Mixture.pdf'))[:12000]
            record['original_excerpt'] = excerpt
            record['original_url'] = 'https://www.cs.toronto.edu/~hinton/absps/tr-96-1.pdf'
            path.write_text(json.dumps(record, indent=2) + '\n')
        if key == 'Viroli2010Mixture':
            start = excerpt.find('Abstract ')
            end = excerpt.find('Article PDF', start)
            excerpt = excerpt[start:end]
        if key == 'Chaloner1995Design':
            excerpt = ''
        if record['provider'] == 'JMLR original':
            excerpt = data['html_text']
        assert abstract or len(excerpt) > 200, key + ' lacks a consulted abstract or source excerpt'
        clean_abstract = BeautifulSoup(abstract or '', 'html.parser').get_text(' ', strip=True)
        notes.extend(['## ' + key, '', '**' + title + '**', '',
                      'Source: ' + (record.get('original_url') or record['source_url']), '',
                      'Consulted scope: ' + ('original full-text excerpt or original abstract page' if excerpt else 'original/retrieved abstract') + '.', '',
                      clean_abstract or excerpt[:6000], ''])
        title = BeautifulSoup(title, 'html.parser').get_text(' ', strip=True)
        entry_type = 'article'
        fields = {'author': ' and '.join(authors), 'title': '{' + title + '}', 'year': str(year), 'journal': venue}
        if key == 'Mazumder2010Spectral':
            fields.update(volume='11', pages='2287--2322')
        doi = crossref.get('DOI') or data.get('externalIds', {}).get('DOI')
        if doi:
            fields['doi'] = doi
        bibtex.append('@' + entry_type + '{' + key + ',\n' + ',\n'.join('  ' + field + ' = {' + latex(value) + '}' for field, value in fields.items()) + '\n}\n')
        records.append({'id': 'ref.verified.' + key, 'paper_id': record['identifier'], 'citation_key': key,
                        'title': title, 'year': year, 'venue': venue,
                        'query': 'Exact permitted original: ' + title, 'source_url': record['source_url'],
                        'retrieved_at': record['retrieved_at'], 'reading_record': str(path.relative_to(ROOT)),
                        'consulted_scope': 'abstract or original excerpt; see literature/reading_notes.md'})
    assert 25 <= len(records) <= 30, len(records)
    (ROOT / 'references.bib').write_text('\n'.join(bibtex))
    (ROOT / 'references_provenance.json').write_text(json.dumps({'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'count': len(records), 'queries': [record['query'] for record in records], 'references': records}, indent=2) + '\n')
    (ROOT / 'literature/reading_notes.md').write_text('\n'.join(notes))
    print('Finalized', len(records), 'consulted references')


if __name__ == '__main__':
    main()
