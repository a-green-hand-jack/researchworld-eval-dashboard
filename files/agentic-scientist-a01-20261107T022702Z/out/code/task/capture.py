"""Standard output-capture compatibility utility."""

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

    def __exit__(self, *exception):
        return self._stack.__exit__(*exception)

    def get_output(self):
        return self.stdout.getvalue(), self.stderr.getvalue()
