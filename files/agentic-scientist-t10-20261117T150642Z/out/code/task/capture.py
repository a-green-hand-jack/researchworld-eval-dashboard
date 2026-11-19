"""Safe compatibility output collector, separate from scientific evaluation."""

import contextlib
import io


class OutputCapture:
    """Capture stdout and stderr as a context manager."""

    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self._stack = None

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self.stdout))
        self._stack.enter_context(contextlib.redirect_stderr(self.stderr))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._stack.__exit__(exc_type, exc_value, traceback)

    def get_output(self):
        return self.stdout.getvalue()

    def get_error(self):
        return self.stderr.getvalue()
