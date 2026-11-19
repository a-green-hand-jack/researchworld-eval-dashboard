import datetime
import json
import sys
from pathlib import Path

event = {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'scope': 'paper', 'step': sys.argv[1], 'summary': sys.argv[2],
         'evidence': sys.argv[3], 'next_action': sys.argv[4]}
markdown = '\n### ' + event['timestamp'] + ' — ' + event['step'] + '\n'
markdown += '\n'.join('- ' + key + ': ' + event[key] for key in ['summary', 'evidence', 'next_action']) + '\n'
for path in [Path('memory.md'), Path('global_memory').resolve() / 'memory.md']:
    with path.open('a') as handle:
        handle.write(markdown)
with (Path('global_memory').resolve() / 'memory.jsonl').open('a') as handle:
    handle.write(json.dumps(event, ensure_ascii=False) + '\n')
