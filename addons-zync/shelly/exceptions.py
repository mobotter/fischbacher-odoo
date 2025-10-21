class ShellExecuteError(Exception):
    def __init__(self, msg, exit_code, stdout, stderr):
        super().__init__(msg)
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


class HandledProcessOutputException(Exception):
    """
    Easily raise output of process.
    """

    def __init__(self, proc):
        self.exit_code = proc["exit_code"]
        self.console = proc["stdout"] + "\n" + proc["stderr"]
