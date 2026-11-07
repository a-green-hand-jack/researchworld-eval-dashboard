"""Prepare an isolated exact-source replay for missing whole-command CPU costs.

Copies only frozen code/config/pilot split provenance, symlinks immutable raw
inputs, and creates no target prediction/scoring job or primary-cache mutation.
"""
import pathlib,shutil
from benchsmall.pipeline import check_freeze
root=pathlib.Path(__file__).resolve().parents[1];check_freeze(root)
target=root.parent/'source-timing-replay'
assert not target.exists(),'Never silently reuse an earlier measurement workspace'
target.mkdir()
for name in ['src','scripts','tests','config','diagnostics']:
 shutil.copytree(root/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
(target/'data').mkdir();(target/'data/raw').symlink_to(root/'data/raw',target_is_directory=True)
(target/'results/pilot').mkdir(parents=True)
shutil.copy2(root/'results/pilot/diagnostics.json',target/'results/pilot/diagnostics.json')
check_freeze(target)
print(str(target))
