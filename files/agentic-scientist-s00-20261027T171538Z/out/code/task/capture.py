"""Bounded stdout/stderr capture helper (harness compatibility artifact).

`OutputCapture` is a context manager that tees text written to ``sys.stdout``
and ``sys.stderr`` into bounded in-memory buffers. It never touches the
filesystem and never writes into a results directory.
"""

import io
import sys


class _BoundedTee(io.TextIOBase):
    def __init__(self, passthrough, limit):
        self._passthrough = passthrough
        self._limit = int(limit)
        self._parts = []
        self._size = 0
        self.truncated = False

    def writable(self):
        return True

    def write(self, text):
        if not isinstance(text, str):
            text = str(text)
        if self._passthrough is not None:
            self._passthrough.write(text)
        room = self._limit - self._size
        if room > 0:
            kept = text[:room]
            self._parts.append(kept)
            self._size += len(kept)
            if len(kept) < len(text):
                self.truncated = True
        elif text:
            self.truncated = True
        return len(text)

    def flush(self):
        if self._passthrough is not None:
            self._passthrough.flush()

    def getvalue(self):
        return "".join(self._parts)


class OutputCapture:
    """Capture (and optionally pass through) stdout/stderr text, bounded in size."""

    def __init__(self, max_chars=1 << 20, passthrough=True):
        self.max_chars = int(max_chars)
        self.passthrough = bool(passthrough)
        self._stdout = None
        self._stderr = None
        self._saved = None

    def __enter__(self):
        self._saved = (sys.stdout, sys.stderr)
        self._stdout = _BoundedTee(sys.stdout if self.passthrough else None, self.max_chars)
        self._stderr = _BoundedTee(sys.stderr if self.passthrough else None, self.max_chars)
        sys.stdout, sys.stderr = self._stdout, self._stderr
        return self

    def __exit__(self, exc_type, exc, tb):
        sys.stdout, sys.stderr = self._saved
        return False

    @property
    def stdout(self):
        return self._stdout.getvalue() if self._stdout is not None else ""

    @property
    def stderr(self):
        return self._stderr.getvalue() if self._stderr is not None else ""

    def get_stdout(self):
        return self.stdout

    def get_stderr(self):
        return self.stderr

    @property
    def truncated(self):
        return bool((self._stdout and self._stdout.truncated) or (self._stderr and self._stderr.truncated))
