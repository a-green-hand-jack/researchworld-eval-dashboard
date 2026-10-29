"""Crossref lookup by title: print top match title/container/year/DOI/first authors (for checking)."""
import sys, json, urllib.request, urllib.parse
for q in sys.argv[1:]:
    u='https://api.crossref.org/works?rows=2&select=title,container-title,issued,DOI,author,type&query.bibliographic='+urllib.parse.quote(q)
    try: d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'research-bot/1.0 (mailto:researcher@institute.ai)'}),timeout=30))
    except Exception as e: print('ERR',q,e); continue
    print('Q:',q)
    for it in d['message']['items']:
        print('   ',it.get('title'),'|',it.get('container-title'),'|',it['issued']['date-parts'][0][0],'|',it['DOI'],'|',[a.get('family') for a in it.get('author',[])[:3]])
