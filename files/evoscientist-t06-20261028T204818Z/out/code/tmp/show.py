import json
for f in ["tmp/iclr.json","tmp/iclr_arch.json"]:
    print(f,[d['name'] for d in json.load(open(f))])
for f in ["tmp/pj_llm-judges.json","tmp/pj_llm-judges-prob-avg.json"]:
    for x in json.load(open(f)): print(x['path'],x.get('size'))
