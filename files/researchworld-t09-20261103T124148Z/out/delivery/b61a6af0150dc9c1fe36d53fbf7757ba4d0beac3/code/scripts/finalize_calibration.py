"""Close remaining imbalance, summary/output and reproduction cost evidence."""
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

out=Path('notes/calibration_finalization.json')
records=[]
commands=[
 [sys.executable,'-u','-m','gatebench.run','configs/pilot_imbalance.json'],
 [sys.executable,'-m','gatebench.summarize','results/pilot_imbalance','--output','results/pilot_imbalance_summary']]
for command in commands:
    start=time.perf_counter();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    subprocess.run(command,check=True)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    records.append(dict(command=command,wall_seconds=time.perf_counter()-start,
                        cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                        peak_rss_kib=after.ru_maxrss))
    out.write_text(json.dumps(records,indent=2))
    print('HUTIAN_WAKE: final calibration stage '+json.dumps(records[-1]),flush=True)
