"""Bounded stdout/stderr capture helper (harness compatibility artifact)."""
import contextlib
import io
import sys


class _Bounded(io.StringIO):
    def __init__(self, limit):
        super().__init__()
        self.limit = limit
        self.dropped = 0

    def write(self, text):
        room = self.limit - self.tell()
        if room <= 0:
            self.dropped += len(text)
            return len(text)
        if len(text) > room:
            self.dropped += len(text) - room
            text = text[:room]
        return super().write(text)


class OutputCapture:
    """Context manager capturing stdout and stderr into bounded in-memory buffers."""

    def __init__(self, limit=1 << 20):
        self.stdout_buffer = _Bounded(limit)
        self.stderr_buffer = _Bounded(limit)
        self._stack = None

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self.stdout_buffer))
        self._stack.enter_context(contextlib.redirect_stderr(self.stderr_buffer))
        return self

    def __exit__(self, exc_type, exc, tb):
        self._stack.close()
        self._stack = None
        return False

    @property
    def stdout(self):
        return self.stdout_buffer.getvalue()

    @property
    def stderr(self):
        return self.stderr_buffer.getvalue()

    def getvalue(self):
        return self.stdout + self.stderr
