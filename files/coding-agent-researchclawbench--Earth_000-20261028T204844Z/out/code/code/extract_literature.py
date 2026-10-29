"""Extract supplied PDFs and optionally fetch the primary GlaMBIE methods paper."""
from pathlib import Path
from html.parser import HTMLParser
import urllib.request
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/literature'
OUT.mkdir(parents=True, exist_ok=True)


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'li', 'div', 'br'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = max(0, self.skip - 1)
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'li', 'div'):
            self.parts.append('\n')

    def handle_data(self, text):
        if not self.skip:
            self.parts.append(text)


def main():
    for path in sorted((ROOT / 'related_work').glob('*.pdf')):
        reader = PdfReader(path)
        (OUT / f'{path.stem}.txt').write_text('\n\n'.join(p.extract_text() for p in reader.pages))
    html = OUT / 'glambie_article.html'
    if not html.exists():
        try:
            with urllib.request.urlopen('https://www.nature.com/articles/s41586-024-08545-z', timeout=30) as response:
                html.write_bytes(response.read())
        except Exception as exc:
            print(f'Optional primary-paper download failed: {exc}')
    if html.exists():
        parser = TextParser()
        parser.feed(html.read_text())
        (OUT / 'glambie_article.txt').write_text('\n'.join(s.strip() for s in ''.join(parser.parts).splitlines() if s.strip()))


if __name__ == '__main__':
    main()
