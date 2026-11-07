"""Verify provenance and final PDF integrity without rerunning inference."""
import collections, hashlib, json, pathlib, sys
import numpy as np
from pypdf import PdfReader
from infer import configurations,make_prompt

ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    qs=json.loads((ROOT/'data/questions.json').read_text());cs=configurations()
    seen=set();matrix=np.full((2048,24),-1,dtype=np.int8);audit_times=[]
    tokens=0;computed=0;first=None;last=None
    for line in (ROOT/'data/responses.jsonl').open():
        r=json.loads(line);key=(r['position'],r['candidate']);assert key not in seen;seen.add(key)
        q=qs[key[0]];c=cs[key[1]];prompt,order=make_prompt(q,c)
        assert hashlib.sha256(prompt.encode()).hexdigest()==r['prompt_sha256']
        assert r['prediction_index']==order[ord(r['answer'])-65]
        assert r['correct']==int(r['prediction_index']==q['answer_index'])
        assert not r['truncated'];assert r['tokens_predicted']==1
        matrix[key]=r['correct'];tokens+=r['tokens_evaluated'];computed+=r['timings']['prompt_n']
        now=r['completed_utc'];first=min(first or now,now);last=max(last or now,now)
        if q['split']=='audit':audit_times.append(now)
    assert len(seen)==2048*24 and (matrix>=0).all()
    frozen=json.loads((ROOT/'logs/locked_choice.json').read_text())
    assert frozen['audit_responses_observed']==0
    assert frozen['candidate']==int(np.argmax(matrix[:128].mean(axis=0)))
    assert frozen['frozen_utc']<min(audit_times)
    saved=np.load(ROOT/'data/correctness.npz')['correct'];assert np.array_equal(matrix,saved)
    pdf=PdfReader(ROOT/'paper.pdf');text=[p.extract_text() for p in pdf.pages]
    # Main text can occupy at most eight pages. Check the actual final sentence,
    # not merely where the uncounted impact statement begins.
    import re
    normalized=[re.sub(r'\s+',' ',t) for t in text]
    body_end=[i+1 for i,t in enumerate(normalized) if 'does not answer that question.' in t]
    assert body_end and body_end[0]<=8,('Main body exceeds eight pages',body_end)
    impact_pages=[i+1 for i,t in enumerate(text) if '\nImpact Statement\n' in '\n'+t+'\n']
    if not impact_pages:
        impact_pages=[i+1 for i,t in enumerate(text) if 'Impact Statement' in t and i<10]
    assert impact_pages and impact_pages[0]<=9,('Body may exceed eight pages',impact_pages)
    assert 'Completed Reproducibility and Ethics Checklist' in '\n'.join(text)
    forbidden=['??','undefined','TODO','PLACEHOLDER','AUTHORERR']
    for word in forbidden:assert word not in '\n'.join(text),word
    report=dict(responses=len(seen),questions=len(qs),candidates=len(cs),
        prompt_tokens_including_cached=tokens,prompt_tokens_computed=computed,
        first_response_utc=first,last_response_utc=last,
        audit_first_response_utc=min(audit_times),choice_frozen_utc=frozen['frozen_utc'],
        pdf_pages=len(pdf.pages),impact_statement_page=impact_pages[0],
        body_final_page=body_end[0],
        checks='all provenance and integrity assertions passed')
    (ROOT/'logs/verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
