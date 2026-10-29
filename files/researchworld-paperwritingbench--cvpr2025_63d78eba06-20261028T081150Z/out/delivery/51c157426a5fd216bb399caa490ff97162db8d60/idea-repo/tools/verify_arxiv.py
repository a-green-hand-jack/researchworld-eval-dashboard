"""Fetch arXiv metadata for candidate ids (batch) and print title/authors/date/journal_ref/doi for checking."""
import sys, json, urllib.request, xml.etree.ElementTree as ET
ids = json.load(open(sys.argv[1]))
ns = {'a':'http://www.w3.org/2005/Atom','x':'http://arxiv.org/schemas/atom'}
out = {}
for i in range(0, len(ids), 20):
    chunk = ids[i:i+20]
    url = 'https://export.arxiv.org/api/query?max_results=%d&id_list=%s' % (len(chunk), ','.join(chunk))
    import time
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'research-bot/1.0 (mailto:researcher@institute.ai)'})
            data = urllib.request.urlopen(req, timeout=60).read(); break
        except Exception as ex:
            print('retry', attempt, ex, file=sys.stderr); time.sleep(10*(attempt+1))
    root = ET.fromstring(data)
    for e in root.findall('a:entry', ns):
        aid = e.find('a:id', ns).text.split('/abs/')[1]
        aid = aid.rsplit('v',1)[0]
        g = lambda t: (e.find(t, ns).text or '').strip().replace('\n',' ') if e.find(t, ns) is not None else ''
        out[aid] = dict(title=' '.join(g('a:title').split()),
            authors=[a.find('a:name', ns).text for a in e.findall('a:author', ns)],
            published=g('a:published')[:10], journal_ref=g('x:journal_ref'), doi=g('x:doi'))
    import time; time.sleep(3.5)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
for k, v in out.items(): print(k, '|', v['title'], '|', v['published'], '|', v['journal_ref'], '|', v['authors'][:2])
