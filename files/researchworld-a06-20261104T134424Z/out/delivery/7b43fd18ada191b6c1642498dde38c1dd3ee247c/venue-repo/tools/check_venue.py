#!/usr/bin/env python3
"""Check a built NeurIPS 2026 submission against the venue requirements in VENUE.md.

Usage:  python3 -I tools/check_venue.py <dir-with-sty-and-tex> <paper.pdf> [<main.tex>]

Checks: V1 style file unmodified (sha256 vs venue/neurips2026/SHA256SUMS), V2 main-text page
count (page where the References heading starts), V3 checklist present, 16 questions answered,
no TODO left, V4 anonymous build (line numbers / no 'Preprint' footer), V5 required sections.
Exit status 1 if any FAIL. WARN lines need a human look.
"""
import hashlib, os, re, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
ref = os.path.join(here, '..', 'venue', 'neurips2026')
fails = 0

def report(level, msg):
    global fails
    if level == 'FAIL':
        fails += 1
    print(f'{level}: {msg}')

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

if len(sys.argv) < 3:
    sys.exit(__doc__)
d, pdf = sys.argv[1], sys.argv[2]
sums = dict(l.split()[::-1] for l in open(os.path.join(ref, 'SHA256SUMS')) if l.strip())

# V1
sty = os.path.join(d, 'neurips_2026.sty')
if not os.path.exists(sty):
    report('FAIL', 'V1 neurips_2026.sty missing')
elif sha(sty) != sums['neurips_2026.sty']:
    report('FAIL', 'V1 neurips_2026.sty differs from the official file')
else:
    report('OK', 'V1 style file identical to official')

# V2
n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
pages = []
for p in range(1, n + 1):
    pages.append(subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), '-layout', pdf, '-'], capture_output=True, text=True).stdout)
refp = next((i + 1 for i, t in enumerate(pages) if re.search(r'^\s*(\d+\s+)?(References|Bibliography)\s*$', t, re.M)), None)
if refp is None:
    report('FAIL', 'V2/V5 no References heading found')
elif refp <= 9:
    report('OK', f'V2 References start on page {refp}; main text <= 9 pages (total pdf pages {n})')
elif refp == 10:
    report('WARN', 'V2 References start on page 10: confirm that all main-text content ends on page 9 (only references/acknowledgments may be on 10)')
else:
    report('FAIL', f'V2 References start on page {refp} > 10: main text exceeds 9 pages')

full = '\n'.join(pages)
# V3
if not re.search(r'NeurIPS Paper Checklist', full):
    report('FAIL', 'V3 checklist heading missing')
else:
    tail = full[full.rfind('NeurIPS Paper Checklist'):]
    if 'TODO' in tail:
        report('FAIL', 'V3 checklist still contains TODO')
    k = len(re.findall(r'Answer:\s*\[(Yes|No|N/A)\]', tail))
    report('OK' if k == 16 else 'FAIL', f'V3 checklist answers found: {k} (expected 16)')
    if 'BEGIN INSTRUCTIONS' in full or 'Delete this instruction block' in tail:
        report('FAIL', 'V3 checklist instruction block not deleted')
    ck = os.path.join(d, 'checklist.tex')
    if os.path.exists(ck):
        norm = lambda s: re.sub(r'\s+', ' ', s)
        q_ref = re.findall(r'Question: (.*?)\n', open(os.path.join(ref, 'checklist.tex')).read())
        q_new = norm(open(ck).read())
        miss = [q for q in q_ref if norm(q) not in q_new]
        report('OK' if not miss else 'FAIL', f'V3 checklist questions unmodified' if not miss else f'V3 {len(miss)} checklist question(s) altered/missing')

# V4
first = pages[0]
if re.search(r'^\s*Preprint\. Work in progress\.\s*$', '\n'.join(l for l in first.splitlines()), re.M):
    report('FAIL', 'V4 preprint option used; submission build must omit it')
if len(re.findall(r'^\s*\d{1,3}\s{2,}\S', pages[0], re.M)) < 5:
    report('WARN', 'V4 no line numbers found on page 1 (are `final`/`preprint` set? anonymous submission build expected)')
else:
    report('OK', 'V4 line numbers present (submission mode)')

# V5
for name, pat in [('Abstract', r'Abstract'), ('Introduction', r'Introduction'), ('Related work', r'Related [Ww]ork'),
                  ('Method', r'Method|Approach|Framework|Setup'), ('Experiments', r'Experiment'),
                  ('Discussion/Limitations', r'Limitation'), ('References', r'References')]:
    report('OK' if re.search(pat, full) else 'FAIL', f'V5 section: {name}')
sys.exit(1 if fails else 0)
