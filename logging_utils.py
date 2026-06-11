"""
logging_utils.py
----------------
Structured logging middleware for the notification platform.
Wraps Python's standard logging with structured key-value output,
request timing, and consistent log levels.
"""

import logging
import time
import functools
from datetime import datetime, timezone


class StructuredLogger:
    """
    A thin wrapper around Python's logging.Logger that emits
    structured key=value log lines for easy parsing and filtering.
    """

    def __init__(self, name: str, level: int = logging.DEBUG):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            formatter = logging.Formatter(
                fmt="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    # ── internal ──────────────────────────────────────────────────────

    def _format(self, message: str, **kwargs) -> str:
        """Append key=value pairs to the message."""
        if not kwargs:
            return message
        pairs = "  ".join(f"{k}={v!r}" for k, v in kwargs.items())
        return f"{message}  {pairs}"

    # ── public API ────────────────────────────────────────────────────

    def debug(self, message: str, **kwargs):
        self._logger.debug(self._format(message, **kwargs))

    def info(self, message: str, **kwargs):
        self._logger.info(self._format(message, **kwargs))

    def warning(self, message: str, **kwargs):
        self._logger.warning(self._format(message, **kwargs))

    def error(self, message: str, **kwargs):
        self._logger.error(self._format(message, **kwargs))

    def critical(self, message: str, **kwargs):
        self._logger.critical(self._format(message, **kwargs))


def get_logger(name: str, level: int = logging.DEBUG) -> StructuredLogger:
    """
    Factory: returns a StructuredLogger for the given module name.

    Usage:
        from logging_utils import get_logger
        logger = get_logger("priority_inbox")
        logger.info("Starting", component="priority_inbox")
    """
    return StructuredLogger(name, level)


def log_execution_time(logger: StructuredLogger):
    """
    Decorator: logs the execution time of a function.

    Usage:
        @log_execution_time(logger)
        def my_function():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            logger.debug(f"Entering {func.__name__}")
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    f"Completed {func.__name__}",
                    elapsed_ms=f"{elapsed_ms:.2f}",
                )
                return result
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    f"Failed {func.__name__}",
                    error=str(exc),
                    elapsed_ms=f"{elapsed_ms:.2f}",
                )
                raise
        return wrapper
    return decorator
