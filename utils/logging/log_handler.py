import logging
from typing import Callable


class LogHandler(logging.Handler):
    """
    Logging handler that copies all log writes to the visible PATCHER LOG widget

    Widget text can be dumped to a file via EXPORT LOG to easily share the exact logs associated with a problem
    """

    def __init__(self, log_cb: Callable[[str, str], None]) -> None:
        super().__init__()
        self.log_callback = log_cb


    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)

            # Choose color tag based on level
            if record.levelno >= logging.ERROR:
                tag = "red"
            elif record.levelno >= logging.WARNING:
                tag = "orange"
            elif record.levelno >= logging.INFO:
                tag = "green"
            else:
                tag = ""

            # Thread-safe UI update via callback
            self.log_callback(msg, tag)

        except Exception:
            self.handleError(record)