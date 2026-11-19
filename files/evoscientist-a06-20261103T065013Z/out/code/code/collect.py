"""Run real endpoint inference. Resume-safe JSONL cache; never send gold fields."""
import concurrent.futures as cf
import datetime,hashlib,json,os,pathlib,re,time,urllib.request,urllib.error
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
def parse_answer(text, options):
    markers=re.findall(r'ANSWER\s*:\s*([A-J])\b',text,re.I)
    lines=text.strip().splitlines()
    final=re.fullmatch(r'\s*ANSWER\s*:\s*([A-J])\s*[.]?\s*',lines[-1],re.I) if lines else None
    if len(markers)!=1 or final is None: return None
    ans=final.group(1).upper()
    return ans if ord(ans)-65<len(options) else None

def main():
    cfg=json.loads((ROOT/'data/config.json').read_text()); items=json.loads((ROOT/'data/cohort.json').read_text())
    cache=ROOT/'data/responses.jsonl'; errorlog=ROOT/'artifacts/transport_errors.jsonl'
    done={}
    if cache.exists():
      for line in cache.read_text().splitlines():
        r=json.loads(line); done[(r['row'],r['prompt_id'])]=r
    jobs=[(i,j) for i in range(cfg['N']) for j in range(cfg['K']) if (i,j) not in done]
    np.random.default_rng(6601).shuffle(jobs)
    base=os.environ['OPENAI_BASE_URL'].rstrip('/'); key=os.environ['OPENAI_API_KEY']
    def call(ij):
      i,j=ij; item=items[i]; prompt=cfg['prompts'][j]['instruction'].format(category=item['category'])
      text=prompt+'\n\nQuestion: '+item['question']+'\n'+'\n'.join(chr(65+k)+'. '+v for k,v in enumerate(item['options']))
      payload={'model':cfg['model'],'messages':[{'role':'user','content':text}],'temperature':cfg['temperature'],'max_tokens':cfg['max_tokens']}
      body=json.dumps(payload).encode(); errors=[]
      for attempt in range(4):
       start=time.time()
       req=urllib.request.Request(base+'/chat/completions',data=body,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
       try:
        with urllib.request.urlopen(req,timeout=120) as res: raw=res.read()
        result=json.loads(raw)
        if 'choices' not in result or not result['choices']: raise ValueError('No completion choices: '+raw.decode()[:200])
        response=result['choices'][0]['message'].get('content') or ''
        ans=parse_answer(response,item['options'])
        row={'row':i,'question_id':item['question_id'],'prompt_id':j,'request':payload,'request_sha256':hashlib.sha256(body).hexdigest(),'response':result,'response_sha256':hashlib.sha256(raw).hexdigest(),'parsed':ans,'correct':int(ans==item['answer']),'format_failure':ans is None,'latency_s':time.time()-start,'attempt':attempt+1,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        return row,errors
       except Exception as e:
        errors.append({'row':i,'prompt_id':j,'attempt':attempt+1,'error':repr(e),'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        time.sleep(2**attempt)
      return None,errors
    start=time.time(); print('pending',len(jobs),flush=True)
    with cf.ThreadPoolExecutor(max_workers=8) as pool,cache.open('a',buffering=1) as out,errorlog.open('a',buffering=1) as err:
     for row,errors in pool.map(call,jobs):
      for e in errors: err.write(json.dumps(e)+'\n')
      if row is not None:
       out.write(json.dumps(row,ensure_ascii=False)+'\n');done[(row['row'],row['prompt_id'])]=row
      if len(done)%100==0:print('complete',len(done),'wall_s',round(time.time()-start,1),flush=True)
    missing=cfg['N']*cfg['K']-len(done)
    usage={'wall_s_this_invocation':time.time()-start,'completed':len(done),'missing':missing,'prompt_tokens':sum(r['response'].get('usage',{}).get('prompt_tokens',0) for r in done.values()),'completion_tokens':sum(r['response'].get('usage',{}).get('completion_tokens',0) for r in done.values()),'format_failures':sum(r['format_failure'] for r in done.values()),'returned_models':sorted(set(r['response'].get('model','unknown') for r in done.values())),'currency_cost':None}
    (ROOT/'artifacts/inference_usage.json').write_text(json.dumps(usage,indent=2));print(usage,flush=True)
    if missing: raise SystemExit('Incomplete inference cache; resume or report incomplete')
if __name__=='__main__':main()
