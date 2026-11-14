"""Standard compatibility helper: capture text written to stdout/stderr within a context."""

import io
import sys


class OutputCapture:
    """Context manager that collects stdout and stderr text in memory."""

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

    def get_stdout(self):
        return self.stdout.getvalue()

    def get_stderr(self):
        return self.stderr.getvalue()
