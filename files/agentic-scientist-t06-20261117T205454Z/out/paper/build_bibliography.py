import datetime
import json
from pathlib import Path
from retrieve_exact_references import ARXIV, DOIS, plain


def escape(value):
    return plain(value).replace('&', r'\&').replace('_', r'\_').replace('%', r'\%')


def main():
    references = []
    entries = []
    keys = list(DOIS) + list(ARXIV)
    for key in keys:
        record = json.loads(Path('literature', key + '.json').read_text())
        authors = []
        for author in record['author']:
            authors.append(author.get('name') or (author.get('family', '') + ', ' + author.get('given', '')))
        year = record.get('year') or record['published']['date-parts'][0][0]
        title = plain(record['title'][0])
        fields = {'author': escape(' and '.join(authors)), 'title': '{' + escape(title) + '}', 'year': str(year)}
        if record.get('DOI'):
            fields['doi'] = record['DOI']
            for original, target in [('container-title', 'journal'), ('volume', 'volume'), ('issue', 'number'), ('page', 'pages')]:
                value = record.get(original)
                if value:
                    fields[target] = escape(value[0] if isinstance(value, list) else value)
            kind = 'book' if record['type'] in ('book', 'monograph') else 'article'
            if kind == 'book':
                fields.pop('journal', None)
                fields['publisher'] = escape(record['publisher'])
        else:
            kind = 'misc'
            fields['howpublished'] = 'arXiv:' + record['arxiv']
        entries.append('@' + kind + '{' + key + ',\n' + ',\n'.join('  ' + name + ' = {' + value + '}' for name, value in fields.items()) + '\n}\n')
        identity = record.get('DOI') or ('arxiv:' + record['arxiv'])
        references.append({'id': 'ref.' + key, 'paper_id': identity, 'citation_key': key,
                           'title': title, 'year': year, 'query': identity,
                           'source_url': record['source_url'],
                           'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           'consulted_artifact': 'literature/' + key + '.json',
                           'consultation_level': 'abstract' if record.get('abstract') else 'bibliographic record only'})
    url = 'https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/README.md'
    entries.append('@misc{NBAdata,\n  author = {{FiveThirtyEight}},\n  title = {{Historical NBA Elo}},\n  year = {2025},\n  howpublished = {Dataset documentation, pinned repository snapshot},\n  url = {' + url + '}\n}\n')
    references.append({'id': 'ref.NBAdata', 'paper_id': 'fivethirtyeight/data:4c1ff5e3aef1816ae04af63218015066e186c147:nba-elo',
                       'citation_key': 'NBAdata', 'title': 'Historical NBA Elo', 'year': 2025,
                       'query': url, 'source_url': url, 'consulted_artifact': 'literature/NBAdata.md',
                       'consultation_level': 'dataset documentation',
                       'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    assert len(references) == 25
    Path('references.bib').write_text('\n'.join(entries))
    Path('references_provenance.json').write_text(json.dumps({'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'count': len(references), 'queries': [record['query'] for record in references], 'references': references}, indent=2))


if __name__ == '__main__':
    main()
