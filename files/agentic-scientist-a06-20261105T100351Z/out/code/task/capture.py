"""Standard context-managed stdout/stderr compatibility capture."""
import contextlib
import io

class OutputCapture:
    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self._stack = None

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self.stdout))
        self._stack.enter_context(contextlib.redirect_stderr(self.stderr))
        return self

    def __exit__(self, exception_type, exception, traceback):
        return self._stack.__exit__(exception_type, exception, traceback)

    def get_output(self):
        return self.stdout.getvalue(), self.stderr.getvalue()
