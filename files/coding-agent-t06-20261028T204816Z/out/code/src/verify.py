"""Check deliverable integrity, numerical claims, PDF format, and saved witnesses."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import pymupdf
from bt import load
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'

def main():
 data=pd.read_csv(R/'data_summary.csv').set_index('dataset')
 assert data.loc['arena','N']==57477 and data.loc['mt_human','N']==3355 and data.loc['mt_gpt4','N']==2400
 assert data.loc['matched_human','N']==data.loc['matched_gpt4','N']==1814
 a=pd.read_csv(R/'attacks.csv');v=pd.read_csv(R/'witness_validation.csv')
 assert a.k.notna().sum()==len(v)==535
 assert (v.gap< -1e-8).all() and v.grad_norm.max()<2e-5
 main_a=a[(a.scope=='all')&(a.kind=='delete')&(a.boundary==1)].set_index('dataset')
 assert main_a.loc['arena','k']==2 and main_a.loc['mt_human','k']==92
 assert [main_a.loc[f'nba{y}','k'] for y in [2013,2014,2015]]==[5,4,9]
 assert np.isnan(main_a.loc['mt_gpt4','k'])
 # Match exposure/schedule exactly, not just their totals.
 h=load('matched_human');g=load('matched_gpt4')
 for key in ['a','b','cluster']:assert np.array_equal(getattr(h,key),getattr(g,key))
 pdf=pymupdf.open(ROOT/'paper.pdf');impact_page=None
 for i,page in enumerate(pdf):
  text=page.get_text()
  assert 'AUTHORERR' not in text
  assert '\ufffd' not in text
  if text.lstrip().startswith('Impact Statement') or ('Impact Statement' in text and 'Research Process and AI Assistance' in text):
   if impact_page is None:impact_page=i+1
 assert impact_page is not None and impact_page-1<=8,(impact_page,'main-text page limit')
 font_types=sorted(set(font[2] for page in pdf for font in page.get_fonts()))
 assert font_types==['Type1'],font_types
 tex=(ROOT/'paper/main.tex').read_text()
 assert '\\input{generated/numbers}' in tex
 assert '??' not in '\n'.join(p.get_text() for p in pdf)
 assert (ROOT/'paper/icml2026.sty').read_bytes()==(ROOT/'paper/vendor/icml2026.sty').read_bytes()
 log=(ROOT/'paper/main.log').read_text()
 assert 'Overfull \\hbox' not in log and 'undefined references' not in log.lower()
 checks=dict(pdf_pages=len(pdf),main_text_pages=impact_page-1,pdf_bytes=(ROOT/'paper.pdf').stat().st_size,font_types=font_types,validated_witnesses=len(v),max_witness_gradient=float(v.grad_norm.max()),all_source_graphs_connected=bool((pd.read_csv(R/'graph_diagnostics.csv').components==1).all()),pdf_sha256=hashlib.file_digest(open(ROOT/'paper.pdf','rb'),'sha256').hexdigest())
 (R/'deliverable_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
 print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
