"""Standard output-capture helper (harness compatibility artifact)."""

import contextlib
import io


class OutputCapture:
    """Context manager that captures stdout and stderr into in-memory buffers."""

    def __init__(self):
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        self._stack = None

    def __enter__(self):
        self._stack = contextlib.ExitStack()
        self._stack.enter_context(contextlib.redirect_stdout(self.stdout_buffer))
        self._stack.enter_context(contextlib.redirect_stderr(self.stderr_buffer))
        return self

    def __exit__(self, exc_type, exc, tb):
        stack, self._stack = self._stack, None
        if stack is not None:
            stack.close()
        return False

    def get_stdout(self):
        return self.stdout_buffer.getvalue()

    def get_stderr(self):
        return self.stderr_buffer.getvalue()

    def get_output(self):
        return {"stdout": self.get_stdout(), "stderr": self.get_stderr()}
