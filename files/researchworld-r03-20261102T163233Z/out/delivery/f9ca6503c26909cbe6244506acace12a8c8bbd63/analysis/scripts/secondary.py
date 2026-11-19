"""Rerun the secondary table after the SHA-alias audit; then rebuild diagnostics."""
import subprocess
for script,args in [('suite.py',['--secondary']),('diagnostics.py',[]),('summarize.py',[])]:
 subprocess.run(['python3','-u','scripts/'+script]+args,check=True)
