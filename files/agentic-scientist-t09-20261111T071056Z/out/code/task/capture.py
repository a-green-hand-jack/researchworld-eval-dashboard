"""Bounded stdout/stderr capture helper (harness compatibility artifact).

``OutputCapture`` is a context manager that redirects ``sys.stdout`` and ``sys.stderr`` into
in-memory buffers limited to ``limit`` characters each.  It performs no file or network I/O.
"""

import io
import sys


class _BoundedBuffer(io.TextIOBase):
    def __init__(self, limit):
        self._limit = limit
        self._parts = []
        self._size = 0
        self.truncated = False

    def writable(self):
        return True

    def write(self, text):
        if not isinstance(text, str):
            raise TypeError("write() argument must be str")
        room = self._limit - self._size
        if room > 0:
            kept = text[:room]
            self._parts.append(kept)
            self._size += len(kept)
        if len(text) > max(room, 0):
            self.truncated = True
        return len(text)

    def getvalue(self):
        return "".join(self._parts)


class OutputCapture:
    def __init__(self, limit=1 << 20):
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")
        self._limit = limit
        self._saved = None
        self._out = _BoundedBuffer(limit)
        self._err = _BoundedBuffer(limit)

    def start(self):
        if self._saved is not None:
            raise RuntimeError("capture already started")
        self._saved = (sys.stdout, sys.stderr)
        sys.stdout, sys.stderr = self._out, self._err
        return self

    def stop(self):
        if self._saved is not None:
            sys.stdout, sys.stderr = self._saved
            self._saved = None
        return self.stdout, self.stderr

    @property
    def stdout(self):
        return self._out.getvalue()

    @property
    def stderr(self):
        return self._err.getvalue()

    @property
    def truncated(self):
        return self._out.truncated or self._err.truncated

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False
