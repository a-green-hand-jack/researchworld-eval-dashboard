"""Finalize traceable local extracts; does not make network requests."""
import json,pathlib,subprocess,hashlib,datetime
R=pathlib.Path('/work')
subprocess.run(['python',str(R/'literature_extract_metadata.py')],check=True,capture_output=True)
ranges={
 '2406.01574':[(1,340),(358,497)],
 '2310.03714':[(1,610)],
 '2406.11695':[(1,460),(491,830),(1251,1450)],
 '1411.2664':[(1,400)],
 '1502.04585':[(1,600)],
 '1212.6906':[(1,430),(461,710)],
}
versions={'2406.01574':'v6','2310.03714':'v1','2406.11695':'v2','1411.2664':'v3','1502.04585':'v1','1212.6906':'v6'}
m=json.loads((R/'literature_access_manifest.json').read_text())
m['scope']={'allowed_arxiv_ids':list(ranges),'allowed_doi':'10.1214/12-AOS1077','external_literature_searches':0,'related_links_followed':0,'citation_pages_accessed':0,'novelty_assessment':'Not performed; no novelty certification or target-paper inference','scope_note':'ArXiv unversioned direct URLs resolved to revisions of the six original works. These are not later reviews. References within papers were not followed or used as independent sources.'}
m['consultation_log']=[]
for aid,spans in ranges.items():
    src=f'literature_arxiv_{aid}.txt'
    lines=(R/src).read_text().splitlines(keepends=True)
    dest=f'literature_arxiv_{aid}_consulted_extracts.txt'
    text=f'SOURCE: https://arxiv.org/pdf/{aid}\nRESOLVED VERSION: {aid}{versions[aid]}\nEXTRACTION: pypdf 6.21.4; PDF page markers are retained. Line references are to {src}.\nThese are the tool-returned reading windows, not a claim to have read every page of the saved PDF. Internal citations/related-work discussion are not independent evidence and were not followed.\n'
    for lo,hi in spans:
        text+=f'\n===== CONSULTED SOURCE LINES {lo}-{hi} =====\n'+''.join(lines[lo-1:hi])
    (R/dest).write_text(text)
    m['consultation_log'].append({'arxiv_id':aid,'resolved_version':versions[aid],'abstract_and_metadata':f'literature_arxiv_{aid}_abstract_metadata.txt','raw_abs_usage':'Only citation_* meta fields and submission history extracted; no related content or hyperlinks fetched','pdf_text':src,'consulted_line_ranges_1_based_inclusive':spans,'saved_consulted_windows':dest})
for e in m['accesses']:
    if '12-AOS1077' in e['requested_url']:
        e['article_content_available']=False
        if e.get('status')==200:
            e['access_result']='HTTP 200 anti-bot challenge, not article content. Scripts and iframe not fetched.'
m['unavailable']=[{'identifier':'10.1214/12-AOS1077','reason':'DOI redirect resolved; direct original .full and .pdf URLs both returned Incapsula challenge HTML rather than abstract/full text/PDF. No bypass, mirror, metadata API, or alternate identifier used. Omitted from references.bib and substantive claims.'}]
m['local_dependencies']={'pdf_text_extractor':'pypdf 6.21.4 (installed because pdftotext unavailable)','dependency_download_is_not_literature_access':True}
outputs=[]
for name in sorted(x.name for x in R.iterdir() if x.is_file() and x.name.startswith('literature_') and x.name!='literature_access_manifest.json'):
    p=R/name
    outputs.append({'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
m['saved_source_artifacts']=outputs
m['finalized_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(R/'literature_access_manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
print('Saved six consulted-window extracts and updated access manifest. No network requests.')
