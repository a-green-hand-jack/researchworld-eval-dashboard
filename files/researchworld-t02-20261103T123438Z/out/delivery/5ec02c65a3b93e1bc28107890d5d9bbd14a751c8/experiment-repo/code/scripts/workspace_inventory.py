"""Inventory all analysis-owned clones/copies, deduplicating file inodes."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2]
paths=[root]+sorted(x for x in root.parent.glob('experiment-*') if x.is_dir())
seen={};counts={}
for directory in paths:
    files=0;logical=0
    for path in directory.rglob('*'):
        if path.is_file():
            st=path.stat();files+=1;logical+=st.st_size
            seen[(st.st_dev,st.st_ino)]=(st.st_size,st.st_blocks*512)
    counts[str(directory)]=dict(files=files,logical_bytes=logical)
report=dict(generated_utc=datetime.now(timezone.utc).isoformat(),kind='Actual analysis-owned workspace/copy inventory; distinct from delivered archive sizing',paths=counts,unique_inode_logical_bytes=sum(x[0] for x in seen.values()),unique_inode_allocated_bytes=sum(x[1] for x in seen.values()),note='All owned experiment-* clones,immutable runners,manuscript integration copy,final frozen copy and source Git are included;non-atomic scan.Git and filesystem allocation overhead remain distinct from delivered scientific archive.')
a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['unique_inode_logical_bytes'],report['unique_inode_allocated_bytes'])
