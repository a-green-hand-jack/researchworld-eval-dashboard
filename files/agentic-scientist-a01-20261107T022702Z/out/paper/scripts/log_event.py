import datetime
import json
import sys
from pathlib import Path


def log_event(step, summary, evidence, next_action):
    event = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "paper",
        "step": step,
        "summary": summary,
        "evidence": evidence,
        "next_action": next_action,
    }
    text = "\n### {timestamp} — {step}\n{summary}\nEvidence: {evidence}\nNext: {next_action}\n".format(**event)
    for path in [Path("memory.md"), Path("global_memory/memory.md").resolve()]:
        with path.open("a") as stream:
            stream.write(text)
    with Path("global_memory/memory.jsonl").resolve().open("a") as stream:
        stream.write(json.dumps(event) + "\n")


if __name__ == "__main__":
    log_event(*sys.argv[1:])
