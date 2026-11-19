"""Standard compatibility capture; never executes candidate code."""
import contextlib
import io


class OutputCapture:
    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.stack = contextlib.ExitStack()

    def __enter__(self):
        self.stack.enter_context(contextlib.redirect_stdout(self.stdout))
        self.stack.enter_context(contextlib.redirect_stderr(self.stderr))
        return self

    def __exit__(self, *args):
        return self.stack.__exit__(*args)

    def get_output(self):
        return self.stdout.getvalue(), self.stderr.getvalue()
