"""Standard in-memory stdout/stderr compatibility capture."""
import contextlib
import io


class OutputCapture:
    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self._contexts = None

    def __enter__(self):
        self._contexts = contextlib.ExitStack()
        self._contexts.enter_context(contextlib.redirect_stdout(self.stdout))
        self._contexts.enter_context(contextlib.redirect_stderr(self.stderr))
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self._contexts.__exit__(exception_type, exception_value, traceback)

    def get_stdout(self):
        return self.stdout.getvalue()

    def get_stderr(self):
        return self.stderr.getvalue()

    def get_output(self):
        return self.get_stdout() + self.get_stderr()

    @property
    def output(self):
        return self.get_output()
