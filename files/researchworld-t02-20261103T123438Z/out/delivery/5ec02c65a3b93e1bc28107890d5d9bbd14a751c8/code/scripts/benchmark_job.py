"""End-to-end benchmark wrapper including interpreter imports and child CPU use."""
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
start = time.perf_counter()
status = subprocess.run([sys.executable,'-u','code/scripts/run_grid.py',sys.argv[1],sys.argv[2]]).returncode
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
files = [p for p in Path(sys.argv[2]).rglob('*') if p.is_file()]
seen = set()
physical = 0
for path in files:
    stat = path.stat()
    key = (stat.st_dev,stat.st_ino)
    if key not in seen:
        physical += stat.st_size
        seen.add(key)
summary = dict(grid=sys.argv[1],output=sys.argv[2],exit_code=status,
    end_to_end_wall_s=time.perf_counter()-start,child_cpu_s=usage.ru_utime+usage.ru_stime,
    child_peak_rss_kib=usage.ru_maxrss,logical_bytes=sum(p.stat().st_size for p in files),
    unique_inode_bytes=physical,files=len(files))
Path(sys.argv[3]).write_text(json.dumps(summary,indent=2)+'\n')
print('HUTIAN_WAKE: Gate benchmark finished '+json.dumps(summary),flush=True)
raise SystemExit(status)
