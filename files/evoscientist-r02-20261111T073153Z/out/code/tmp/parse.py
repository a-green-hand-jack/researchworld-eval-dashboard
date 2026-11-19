import re,json
t=open('tmp/arx.xml').read()
for e in t.split('<entry>')[1:]:
    print(re.search(r'<id>(.*?)</id>',e).group(1), '|', re.sub(r'\s+',' ',re.search(r'<title>(.*?)</title>',e,re.S).group(1)), '|', re.findall(r'<name>(.*?)</name>',e)[:4], re.search(r'<published>(.*?)</published>',e).group(1)[:10])
for f in ['tmp/c1.json','tmp/c2.json']:
    try:
        m=json.load(open(f))['message']; print(m['title'], m.get('container-title'), m.get('issued'), [a['family'] for a in m['author']][:4])
    except Exception as ex: print(f,ex)
