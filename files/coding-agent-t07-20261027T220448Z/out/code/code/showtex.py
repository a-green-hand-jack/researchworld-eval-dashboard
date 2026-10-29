import re,sys
s=open(sys.argv[1]).read()
s=re.sub(r'\\,\\scriptsize','',s); s=s.replace('\\\\','').replace('--','-').replace('\\multicolumn{2}{c}','').replace('\\multicolumn{1}{c}','')
for l in s.split('\n')[3:]:
    if l.startswith('\\'): continue
    print(l[:int(sys.argv[2]) if len(sys.argv)>2 else 300])
