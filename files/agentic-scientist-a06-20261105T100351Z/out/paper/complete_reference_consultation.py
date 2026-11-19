import hashlib
import html
import json
import re
from pathlib import Path

import pymupdf
import requests


def main():
    provenance = json.loads(Path('references_provenance.json').read_text())
    for reference in provenance['references']:
        citation_key = reference['citation_key']
        path = Path(reference['consultation_path'])
        content = json.loads(path.read_text())
        if citation_key == 'Andrews2018Winners':
            pdf_path = Path('literature/Andrews2018Winners.pdf')
            url = 'https://www.nber.org/system/files/working_papers/w25456/w25456.pdf'
            if not pdf_path.exists():
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                pdf_path.write_bytes(response.content)
            document = pymupdf.open(pdf_path)
            content['consulted_text'] = document[0].get_text() + document[1].get_text()
            reference.update(original_document_path=str(pdf_path), original_document_url=url,
                             consultation_extent='Original NBER PDF title and abstract pages only (first two PDF pages); no references or related works followed.')
        elif citation_key == 'Nadeau2003Inference':
            text = Path('literature/Nadeau2003Inference.html').read_text()
            content['abstract'] = html.unescape(re.search(r'"description":"(.*?)"', text, re.S).group(1))
            reference['consultation_extent'] = 'Original Springer abstract and metadata only; no references or recommendations followed.'
        elif citation_key == 'Varoquaux2018CrossValidation':
            url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
            response = requests.get(url, params={'query': 'DOI:' + content['doi'], 'format': 'json', 'resultType': 'core'}, timeout=60)
            response.raise_for_status()
            records = response.json()['resultList']['result']
            record = next(record for record in records if record['doi'].lower() == content['doi'].lower())
            content['abstract'] = record['abstractText']
            content['original_abstract_record'] = record['pmid']
            reference.update(abstract_source_url=response.url,
                             consultation_extent='Original journal abstract as deposited in PubMed/Europe PMC, retrieved by exact DOI; metadata from Crossref. No citing or related pages followed.')
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + '\n')
        reference['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    Path('references_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


if __name__ == '__main__':
    main()
