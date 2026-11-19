"""Copy this owner's real code/analysis/results into a paper-repo checkout.

Does not copy manuscript/presentation paths and does not create placeholders.
Source and target must be distinct. Called after fetching the paper target.
"""
import argparse
from pathlib import Path
import shutil

p=argparse.ArgumentParser();p.add_argument('target');p.add_argument('--include-pilots',action='store_true');p.add_argument('--include-production',action='store_true')
p.add_argument('--production-panels',nargs='+',choices=['core','noise','imbalance'],default=['core','noise','imbalance'])
a=p.parse_args()
root=Path(__file__).resolve().parents[1];target=Path(a.target).resolve()
if target==root:
    raise ValueError('Source and target must be distinct')
# The settled CODEOWNERS grants these complete subtrees to analysis. Replace
# them atomically at the handoff level so superseded v1 receipts cannot survive
# a directory merge. No manuscript or presentation paths are touched.
for name in ['code','analysis','results']:
    destination=target/name
    if destination.exists():shutil.rmtree(destination)
code=target/'code';code.mkdir(exist_ok=True)
for name in ['src','scripts','configs','tests','data']:
    shutil.copytree(root/name,code/name,dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.gz','*.zip'))
for name in ['pyproject.toml','environment.json','requirements-lock.txt','.gitignore']:
    shutil.copy2(root/name,code/name)
# Working analysis documentation belongs in this owner's analysis/ path.
shutil.copytree(root/'notes',target/'analysis',dirs_exist_ok=True)
results=target/'results';results.mkdir(exist_ok=True)
for source in (root/'results').iterdir():
    if source.name.startswith('checkpoint'):
        # Working partial diagnostics are not a full production handoff.
        continue
    if source.name.startswith('production') and not a.include_production:
        continue
    if source.name.startswith('production_') and source.name.removeprefix('production_') not in a.production_panels:
        continue
    if source.name.startswith('pilot') and not a.include_pilots:
        continue
    if source.name=='pilot_all_summary':
        # This folder is a timing benchmark across overlapping pilot streams.
        # It cannot be used as graph-population accuracy evidence.
        continue
    if source.is_dir():
        shutil.copytree(source,results/source.name,dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.tmp.parquet','*.tmp'))
    else:
        shutil.copy2(source,results/source.name)
shutil.copy2(root/'notes/delivery_reproduction.md',code/'README.md')
print('Exported code/, analysis/ and available results/ to',target)
