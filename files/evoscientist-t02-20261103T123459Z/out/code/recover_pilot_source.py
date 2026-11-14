"""Recover the exact first-pilot source from documented additive instrumentation edits.
This creates an archival file only if its bytes match the hash in all nine early logs.
"""
import hashlib
from pathlib import Path

s=Path('train.py').read_text()
s=s.replace("        if normalization == 'matched_mean':\n            with torch.no_grad():\n                self.readout.mul_(math.sqrt(width))\n",'')
s=s.replace("                  initial_sha256=hashlib.sha256(b''.join(v.numpy().tobytes() for v in initial.values())).hexdigest(),\n",'')
s=s.replace('    cpu_start = time.process_time()\n','')
s=s.replace('                    centered = z - z.mean(1, keepdim=True)\n                    bias = centered.mean(0, keepdim=True)\n                    residual = centered - proj\n','')
a=s.index('                        rule_energy=frac,')
b=s.index('                    rows.append(row)',a)
s=s[:a]+'''                        rule_energy=frac,
                        projected_eval_acc=float((proj[te].argmax(1)==y[te]).float().mean()),
                        residual_train_acc=float(((z-proj)[tr].argmax(1)==y[tr]).float().mean()),
                        logit_rms=float((z-z.mean(1,keepdim=True)).square().mean().sqrt()))
'''+s[b:]
s=s.replace('                 cpu_seconds=time.process_time()-cpu_start,\n','')
s=s.replace("choices=['sqrt','mean','matched_mean']","choices=['sqrt','mean']")
sha=hashlib.sha256(s.encode()).hexdigest()
assert sha=='68c98c0b4067e5bef61ef4603e116d0e72142bd1e88675f1d830057d546e0cda',sha
Path('source_history').mkdir(exist_ok=True)
Path('source_history/train_pilot_v1.py').write_text(s)
print('Recovered exact archived pilot source:',sha)
