import json
import platform
import subprocess
import sys

import numpy as np
import scipy


def code_rev():
    try:
        root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True, cwd=__file__.rsplit("/", 1)[0]).strip()
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=root).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", "code"], text=True, cwd=root).strip())
        return rev + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def meta(**kw):
    from . import data
    d = dict(code_rev=code_rev(), python=sys.version.split()[0], numpy=np.__version__, scipy=scipy.__version__,
             platform=platform.platform(), data_sha256=data.CHECKSUMS, data_sources=data.SOURCES)
    d.update(kw)
    return d


def write_meta(path, **kw):
    with open(path, "w") as f:
        json.dump(meta(**kw), f, indent=1, default=str)
