"""Safe compatibility capture for callers expecting OutputCapture."""

import contextlib
import io


class OutputCapture:
    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self._stack = contextlib.ExitStack()

    def __enter__(self):
        self._stack.enter_context(contextlib.redirect_stdout(self.stdout))
        self._stack.enter_context(contextlib.redirect_stderr(self.stderr))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._stack.__exit__(exc_type, exc_value, traceback)

    def get_output(self):
        return self.stdout.getvalue(), self.stderr.getvalue()
