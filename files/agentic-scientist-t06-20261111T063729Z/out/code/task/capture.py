"""Compatibility artifact: minimal output capture helper (not used by the evaluators)."""
import io
import sys


class OutputCapture:
    """Context manager that captures stdout/stderr text written inside the block."""

    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self._saved = None

    def __enter__(self):
        self._saved = (sys.stdout, sys.stderr)
        sys.stdout, sys.stderr = self.stdout, self.stderr
        return self

    def __exit__(self, exc_type, exc, tb):
        sys.stdout, sys.stderr = self._saved
        return False

    def getvalue(self):
        return {"stdout": self.stdout.getvalue(), "stderr": self.stderr.getvalue()}
