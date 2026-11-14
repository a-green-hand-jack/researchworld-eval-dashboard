"""Standard output-capture compatibility artifact (not used by the evaluators)."""
import io
import sys


class OutputCapture:
    """Capture text written to stdout/stderr inside a ``with`` block."""

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
