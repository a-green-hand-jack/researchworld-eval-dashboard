"""Compatibility helper: capture stdout/stderr text produced inside a ``with`` block."""
import contextlib
import io


class OutputCapture:
    def __init__(self):
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()
        self._stack = None

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self._stdout))
        self._stack.enter_context(contextlib.redirect_stderr(self._stderr))
        return self

    def __exit__(self, exc_type, exc, tb):
        stack, self._stack = self._stack, None
        if stack is not None:
            stack.close()
        return False

    @property
    def stdout(self):
        return self._stdout.getvalue()

    @property
    def stderr(self):
        return self._stderr.getvalue()

    def get_output(self):
        return {"stdout": self.stdout, "stderr": self.stderr}
