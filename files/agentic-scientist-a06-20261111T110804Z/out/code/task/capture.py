"""Bounded text capture helper (harness compatibility artifact)."""
import contextlib
import io
import sys


class OutputCapture:
    """Capture text written to stdout/stderr, keeping at most `limit` characters."""

    def __init__(self, limit=65536):
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")
        self.limit = limit
        self._chunks = []
        self._size = 0
        self.truncated = False
        self._stack = None

    def write(self, text):
        text = str(text)
        room = self.limit - self._size
        if room <= 0:
            self.truncated = self.truncated or bool(text)
            return len(text)
        if len(text) > room:
            self.truncated = True
        piece = text[:room]
        self._chunks.append(piece)
        self._size += len(piece)
        return len(text)

    def flush(self):
        return None

    def getvalue(self):
        return "".join(self._chunks)

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self))
        self._stack.enter_context(contextlib.redirect_stderr(self))
        return self

    def __exit__(self, exc_type, exc, tb):
        stack, self._stack = self._stack, None
        if stack is not None:
            stack.close()
        return False


__all__ = ["OutputCapture"]
