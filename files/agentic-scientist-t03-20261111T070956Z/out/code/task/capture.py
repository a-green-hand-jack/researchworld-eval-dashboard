"""Standard compatibility artifact: minimal bounded output capture for harness tooling."""
import io
import sys


class OutputCapture:
    """Context manager capturing stdout/stderr text with a hard size bound."""

    def __init__(self, limit=1 << 20):
        self.limit = limit
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()
        self._saved = None

    def __enter__(self):
        self._saved = (sys.stdout, sys.stderr)
        sys.stdout, sys.stderr = self._stdout, self._stderr
        return self

    def __exit__(self, *exc):
        sys.stdout, sys.stderr = self._saved
        return False

    @property
    def stdout(self):
        return self._stdout.getvalue()[: self.limit]

    @property
    def stderr(self):
        return self._stderr.getvalue()[: self.limit]
