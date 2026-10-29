"""Harness compatibility artifact: bounded in-process stdout/stderr capture.

``OutputCapture`` is a context manager that temporarily redirects ``sys.stdout`` and
``sys.stderr`` into bounded in-memory buffers.  It never writes files, never touches the
network and keeps at most ``max_bytes`` characters per stream (oldest text is dropped and
``truncated`` is set).  The t06 evaluators do not need it.
"""
import io
import sys


class _BoundedBuffer(io.TextIOBase):
    def __init__(self, max_bytes):
        super().__init__()
        self.max_bytes = int(max_bytes)
        self.parts = []
        self.size = 0
        self.truncated = False

    def writable(self):
        return True

    def write(self, text):
        if not isinstance(text, str):
            text = str(text)
        self.parts.append(text)
        self.size += len(text)
        while self.size > self.max_bytes and self.parts:
            overflow = self.size - self.max_bytes
            head = self.parts[0]
            if len(head) <= overflow:
                self.parts.pop(0)
                self.size -= len(head)
            else:
                self.parts[0] = head[overflow:]
                self.size -= overflow
            self.truncated = True
        return len(text)

    def getvalue(self):
        return "".join(self.parts)


class OutputCapture:
    """Capture stdout/stderr text written inside a ``with`` block (bounded, in memory)."""

    def __init__(self, max_bytes=1 << 20):
        if type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError("max_bytes must be a positive int")
        self.max_bytes = max_bytes
        self._stdout = _BoundedBuffer(max_bytes)
        self._stderr = _BoundedBuffer(max_bytes)
        self._saved = None

    def __enter__(self):
        self._saved = (sys.stdout, sys.stderr)
        sys.stdout, sys.stderr = self._stdout, self._stderr
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._saved is not None:
            sys.stdout, sys.stderr = self._saved
            self._saved = None
        return False

    start = __enter__

    def stop(self):
        self.__exit__(None, None, None)
        return self

    @property
    def stdout(self):
        return self._stdout.getvalue()

    @property
    def stderr(self):
        return self._stderr.getvalue()

    @property
    def truncated(self):
        return self._stdout.truncated or self._stderr.truncated

    def getvalue(self):
        return {"stdout": self.stdout, "stderr": self.stderr, "truncated": self.truncated}
