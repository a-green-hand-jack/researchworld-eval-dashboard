import os,shutil,sys
print('tools', {x:shutil.which(x) for x in ['mutool','gs','pdftohtml','pdfinfo','qpdf','node','python3','java','tesseract']})
print('opt',os.listdir('/opt'))
print('pythonusr',os.path.exists('/usr/bin/python3'))
for p in ['/usr/lib/python3/dist-packages','/usr/local/lib','/root/.cache','/opt/research/lib/python3.11/site-packages']:
    if os.path.isdir(p): print(p, os.listdir(p))
