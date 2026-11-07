import datetime
import html
import json
from pathlib import Path
import re
import time
import urllib.request

from bs4 import BeautifulSoup
from prepare_sources import REFERENCES

ROOT = Path(__file__).resolve().parent
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()

def tex(value):
    replacements = {'&': r'\&', '%': r'\%', '_': r'\_'}
    return ''.join(replacements.get(character, character) for character in str(value))

records = []
bibliography = []
for key, identifier in REFERENCES:
    directory = ROOT / 'literature' / key
    if identifier.startswith('arxiv:'):
        soup = BeautifulSoup((directory / 'abstract.html').read_text(), 'html.parser')
        title = soup.find('meta', attrs={'name': 'citation_title'})['content']
        authors = [node['content'] for node in soup.find_all('meta', attrs={'name': 'citation_author'})]
        year = int(soup.find('meta', attrs={'name': 'citation_date'})['content'][:4])
        abstract = soup.find('blockquote', class_='abstract').get_text(' ', strip=True)
        number = identifier.split(':')[1]
        url = 'https://arxiv.org/abs/' + number
        fields = {'author': ' and '.join(authors), 'title': '{' + tex(title) + '}', 'year': year,
                  'journal': 'arXiv preprint arXiv:' + number, 'url': url}
        entry_type = 'article'
        scope = 'Read the official abstract and downloaded full text where available; citation claims restricted to described method and guarantee scope.'
    else:
        metadata = json.loads((directory / 'metadata.json').read_text())
        title = metadata['title'][0]
        authors = [' '.join([author.get('given', ''), author.get('family', '')]).strip() for author in metadata.get('author', metadata.get('editor', []))]
        if not authors and (directory / 'author_metadata.json').exists():
            authors = [author['author']['display_name'] for author in json.loads((directory / 'author_metadata.json').read_text())['authorships']]
        year = metadata.get('published', metadata.get('issued'))['date-parts'][0][0]
        abstract = BeautifulSoup(metadata.get('abstract', ''), 'html.parser').get_text(' ', strip=True)
        url = 'https://api.crossref.org/works/' + identifier
        if not abstract:
            openalex_path = directory / 'openalex.json'
            if not openalex_path.exists():
                try:
                    endpoint = 'https://api.openalex.org/works/https://doi.org/' + identifier + '?select=id,title,abstract_inverted_index,doi,publication_year'
                    response = urllib.request.urlopen(endpoint, timeout=40).read()
                    openalex_path.write_bytes(response)
                    time.sleep(.6)
                except Exception as error:
                    (directory / 'abstract_failure.txt').write_text(str(error))
            if openalex_path.exists():
                inverted = json.loads(openalex_path.read_text()).get('abstract_inverted_index') or {}
                ordered = {position: word for word, positions in inverted.items() for position in positions}
                abstract = ' '.join(ordered[position] for position in sorted(ordered))
        publisher_path = directory / 'publisher_reading.json'
        publisher_url = None
        if publisher_path.exists():
            publisher_reading = json.loads(publisher_path.read_text())
            if publisher_reading.get('http_status') == 200 and publisher_reading.get('abstract'):
                abstract = publisher_reading['abstract']
                publisher_url = publisher_reading['url']
        if publisher_url:
            url = publisher_url
        fields = {'author': ' and '.join(authors), 'title': '{' + tex(title) + '}', 'year': year, 'doi': identifier}
        if metadata['type'] in ('book', 'monograph', 'edited-book'):
            entry_type = 'book'
            fields['publisher'] = tex(metadata.get('publisher', ''))
        elif metadata['type'] == 'book-chapter':
            entry_type = 'incollection'
            fields['booktitle'] = tex(metadata.get('container-title', [''])[0])
            fields['publisher'] = tex(metadata.get('publisher', ''))
        else:
            entry_type = 'article'
            fields['journal'] = tex(metadata.get('container-title', [''])[0])
        for field in ('volume', 'issue', 'page'):
            if metadata.get(field):
                fields['pages' if field == 'page' else 'number' if field == 'issue' else field] = tex(metadata[field])
        scope = 'Read bibliographic metadata and abstract where supplied. No full-text review or novelty certification claimed.'
    reading = {'title': title, 'abstract': abstract or None, 'reading_scope': scope,
               'source_url': url, 'no_citation_chaining': True}
    (directory / 'reading.json').write_text(json.dumps(reading, indent=2) + '\n')
    bibliography.append('@' + entry_type + '{' + key + ',\n' + '\n'.join('  ' + field + ' = {' + str(value) + '},' for field, value in fields.items()) + '\n}\n')
    records.append({'id': 'ref.' + key, 'paper_id': identifier, 'citation_key': key, 'title': title,
                    'year': year, 'query': 'Direct identifier lookup: ' + identifier, 'source_url': url,
                    'retrieved_at': NOW, 'reading_path': 'literature/' + key + '/reading.json', 'reading_scope': scope})
    print(key, title, '\n', abstract[:1000] if abstract else '[No abstract supplied: bibliographic/background citation only]', flush=True)

original = ROOT / 'literature' / 'original_references.bib'
if not original.exists():
    original.write_bytes((ROOT / 'references.bib').read_bytes())
(ROOT / 'references.bib').write_text('\n'.join(bibliography))
(ROOT / 'references_provenance.json').write_text(json.dumps({'generated_at': NOW, 'count': len(records),
    'queries': [record['query'] for record in records], 'references': records}, indent=2) + '\n')
