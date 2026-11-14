from pathlib import Path
from pypdf import PdfReader
import json
root = Path('/work/literature')
meta = []
for f in sorted(root.glob('*.pdf')):
    r = PdfReader(f)
    pages = [p.extract_text() or '' for p in r.pages]
    (root / (f.stem + '.pages.json')).write_text(json.dumps(pages, ensure_ascii=False))
    meta.append({'id': f.stem, 'pages': len(pages), 'metadata': str(r.metadata)})
    print('\n===== ' + f.stem + ' PDF PAGE 1 of ' + str(len(pages)) + ' =====\n' + pages[0])
(root / 'pdf_metadata.json').write_text(json.dumps(meta, indent=2))
