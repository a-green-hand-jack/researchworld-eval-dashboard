"""Standard compatibility artifact: bounded stdout/stderr capture helper."""
import contextlib
import io
import sys


class OutputCapture:
    """Context manager that captures text written to stdout and stderr (bounded)."""

    def __init__(self, limit=1 << 20):
        self.limit = int(limit)
        self._out = io.StringIO()
        self._err = io.StringIO()
        self._stack = None

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self._out))
        self._stack.enter_context(contextlib.redirect_stderr(self._err))
        return self

    def __exit__(self, exc_type, exc, tb):
        self._stack.close()
        self._stack = None
        return False

    @property
    def stdout(self):
        return self._out.getvalue()[: self.limit]

    @property
    def stderr(self):
        return self._err.getvalue()[: self.limit]

    def write_through(self):
        sys.stdout.write(self.stdout)
        sys.stderr.write(self.stderr)
