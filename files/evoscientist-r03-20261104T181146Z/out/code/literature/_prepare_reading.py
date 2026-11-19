import re
from pathlib import Path
from _offline_pdf_text import PDF
for id in ['2210.07316','2402.14992','2407.12844','2405.10938','2412.06540']:
    pdf=PDF('literature/'+id+'.pdf'); out=[]
    for i in range(1,len(pdf.pages)+1):
        t=pdf.page(i)
        m=re.search(r'(?mi)^\s*(?:References|REFERENCES|R E F E R E N C E S)\s*$',t)
        if m: t=t[:m.start()]
        out.append('\n=== PDF PAGE '+str(i)+' ===\n'+t)
        print(id,i,' | '.join(re.findall(r'(?m)^[0-9]+(?:\.[0-9]+)?\.? [A-Z][^\n]{2,80}$',t))[:240])
        if m:
            print('Bibliography excluded from page',i)
            break
    Path('literature/'+id+'.body.txt').write_text(''.join(out))
