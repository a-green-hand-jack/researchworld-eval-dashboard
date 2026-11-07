"""Verify delivered evidence, manuscript references, page cap, and secret hygiene."""
import hashlib,json,os,pathlib,re,subprocess
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    cfg=json.loads((ROOT/'data/config.json').read_text());cohort=json.loads((ROOT/'data/cohort.json').read_text());records=[json.loads(s) for s in (ROOT/'data/responses.jsonl').read_text().splitlines()]
    assert len(cohort)==600 and len({x['question_id'] for x in cohort})==600
    assert all(x['answer']==chr(65+x['answer_index']) and 0<=x['answer_index']<len(x['options']) for x in cohort)
    assert len(records)==cfg['N']*cfg['K']==4800
    assert len({(r['row'],r['prompt_id']) for r in records})==4800
    from collect import parse_answer
    from collections import Counter
    counts=Counter()
    for r in records:
      item=cohort[r['row']];assert r['question_id']==item['question_id']
      ans=parse_answer(r['response']['choices'][0]['message'].get('content') or '',item['options']);assert ans==r['parsed'];assert int(ans==item['answer'])==r['correct']
      assert hashlib.sha256(json.dumps(r['request']).encode()).hexdigest()==r['request_sha256']
      assert r['request']['model']==cfg['model'];assert r['request']['temperature']==cfg['temperature'];assert r['request']['max_tokens']==cfg['max_tokens']
      assert set(r['request'])=={'model','messages','temperature','max_tokens'}
      assert len(r['request']['messages'])==1
      j=r['prompt_id'];expected=cfg['prompts'][j]['instruction'].format(category=item['category'])+'\n\nQuestion: '+item['question']+'\n'+'\n'.join(chr(65+k)+'. '+v for k,v in enumerate(item['options']))
      assert expected==r['request']['messages'][0]['content']
      counts['correct']+=r['correct'];counts['format_failures']+=r['format_failure']
    required=['paper.pdf','paper.tex','references.bib','README.md','research_request.md','final_report.md','requirements-lock.txt','sources.md','deviations.md','artifacts/report_card.json','artifacts/synthetic_summary.csv','artifacts/real_summary.csv','artifacts/budget_matched.csv','artifacts/figures/optimism.png','artifacts/figures/coverage_width.png','artifacts/figures/failure_precision.png','artifacts/figures/correlation.png','tests/test_statistics.py','code/run_experiments.py','code/collect.py']
    for name in required:assert (ROOT/name).is_file() and (ROOT/name).stat().st_size>0,name
    # PDF page-cap check conservatively counts disclosure sections too.
    from pypdf import PdfReader
    reader=PdfReader(str(ROOT/'paper.pdf'));pages=[page.extract_text() for page in reader.pages]
    (ROOT/'artifacts/paper-extracted.txt').write_text('\f'.join(pages))
    main_end=None;ref_page=None
    for i,p in enumerate(pages,1):
      if 'ai use statement' in p.lower() and main_end is None:main_end=i
      if re.search(r'^\s*References\s*$',p,re.M|re.I) and ref_page is None:ref_page=i
    assert main_end is not None and main_end<=9,('Main text over 9 pages',main_end)
    log=(ROOT/'paper.log').read_text(errors='replace')
    assert 'undefined references' not in log and 'undefined citations' not in log
    assert 'Citation `' not in log or 'undefined' not in log
    tex=(ROOT/'paper.tex').read_text();assert '\\section*{AI use statement}' in tex
    # Avoid placeholder-shaped artefacts in final manuscript (not legitimate prompt syntax).
    for word in ['TODO','FIXME','TBD','PLACEHOLDER']:
      assert word not in tex,word
    # Raw secrets never printed. Scan only task-produced source/records/docs, not tool infrastructure.
    leaked=[]
    secrets=[os.environ.get('OPENAI_API_KEY','')]
    for folder in ['code','tests','data','artifacts','template']:
      for p in (ROOT/folder).rglob('*'):
       if not p.is_file() or p.suffix in ['.pdf','.png','.parquet','.npy','.npz']:continue
       if p.stat().st_size>30_000_000:continue
       text=p.read_text(errors='ignore')
       for sec in secrets:
        if len(sec)>10 and sec in text:leaked.append(str(p.relative_to(ROOT)))
    assert not leaked,leaked
    result={'status':'PASS','scored_cells':len(records),'format_failures':counts['format_failures'],'main_text_ends_on_page':main_end,'references_begin_page':ref_page,'pdf_pages':len(pages)-int(not pages[-1].strip()),'request_hashes_verified':4800,'scores_recomputed':4800,'secret_matches':0,'selected_target_contract':'finite cohort, population only in simulations','joint_report_card_confidence':.95}
    (ROOT/'artifacts/delivery_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
