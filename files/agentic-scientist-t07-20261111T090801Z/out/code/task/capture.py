"""Bounded stdout/stderr capture helper (harness compatibility artifact)."""

import contextlib
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
            raise TypeError("text required")
        room = self._limit - self._size
        if room > 0:
            piece = text[:room]
            self._parts.append(piece)
            self._size += len(piece)
        if len(text) > max(room, 0):
            self.truncated = True
        return len(text)

    def getvalue(self):
        return "".join(self._parts)


class OutputCapture:
    """Context manager capturing stdout and stderr into bounded in-memory buffers."""

    def __init__(self, max_chars=1_000_000):
        if type(max_chars) is not int or max_chars <= 0:
            raise ValueError("max_chars must be a positive integer")
        self.stdout = _BoundedBuffer(max_chars)
        self.stderr = _BoundedBuffer(max_chars)
        self._stack = None

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self.stdout))
        self._stack.enter_context(contextlib.redirect_stderr(self.stderr))
        return self

    def __exit__(self, exc_type, exc, tb):
        stack, self._stack = self._stack, None
        if stack is not None:
            stack.close()
        return False

    def get_stdout(self):
        return self.stdout.getvalue()

    def get_stderr(self):
        return self.stderr.getvalue()

    @staticmethod
    def passthrough_available():
        return sys.__stdout__ is not None
