# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import re
import sys
import threading
import time
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


class LoggingLevel(IntEnum):
    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class TimedRotatingWhen(StrEnum):
    SECONDS = "S"
    MINUTES = "M"
    HOURS = "H"
    DAYS = "D"
    MIDNIGHT = "midnight"
    WEEKDAY = "W0"

    @classmethod
    def get_weekday(cls, weekday: int) -> str:
        if not 0 <= weekday <= 6:
            raise ValueError("Weekday must be between 0 (Monday) and 6 (Sunday)")
        return f'W{weekday}'


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class LoggerConfig:
    name: str = "app"
    level: LoggingLevel = LoggingLevel.INFO
    console_out: bool = True
    file_out: bool = False
    file_path: str = "./log/app.log"
    message_format: Optional[str] = None
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    timezone_offset: str = "+09:00"
    backup_suffix: str = "%Y%m%d"
    backup_when: TimedRotatingWhen = TimedRotatingWhen.MIDNIGHT
    backup_interval: int = 1
    backup_count: int = 7
    use_utc: bool = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _strftime_to_regex(_format: str) -> re.Pattern:
    mapping = {"%Y": r"\d{4}",              # 4-digit year
               "%y": r"\d{2}",              # 2-digit year
               "%m": r"\d{2}",              # Month (01-12)
               "%d": r"\d{2}",              # Day of month (01-31)
               "%H": r"\d{2}",              # 24-hour (00-23)
               "%I": r"\d{2}",              # 12-hour (01-12)
               "%M": r"\d{2}",              # Minute (00-59)
               "%S": r"\d{2}",              # Second (00-60)
               "%f": r"\d{6}",              # Microsecond (000000-999999)
               "%j": r"\d{3}",              # Day of year (001-366)
               "%U": r"\d{2}",              # Week number (Sunday start, 00-53)
               "%W": r"\d{2}",              # Week number (Monday start, 00-53)
               "%V": r"\d{2}",              # ISO week (01-53)
               "%w": r"\d",                 # Weekday (0-6, Sunday=0)
               "%u": r"\d",                 # ISO weekday (1-7, Monday=1)
               "%G": r"\d{4}",              # ISO year
               "%a": r"[A-Za-z]{3}",        # Abbreviated weekday name
               "%A": r"[A-Za-z]+",          # Full weekday name
               "%b": r"[A-Za-z]{3}",        # Abbreviated month name
               "%B": r"[A-Za-z]+",          # Full month name
               "%p": r"[APap][Mm]",         # AM/PM
               "%Z": r"[A-Za-z_./+\-]+",    # Timezone name (approximate)
               "%z": r"[+\-]\d{2}:?\d{2}",  # ±HHMM or ±HH:MM
               "%%": r"%"}                  # Literal %

    # (Optional) Normalize padding flags like %-m, %_d, %0H to %m, %d, %H
    _format = re.sub(r"%[-_0]([aAbBcdHIjmMpSUwWxXyYZzGGuVvsf%])", r"%\1", _format)
    escaped = re.escape(_format)

    # Replace format specifiers with regex patterns
    for k, v in mapping.items():
        escaped = escaped.replace(re.escape(k), v)

    # Compile regex pattern
    complied = re.compile(rf"^{escaped}$", flags=re.IGNORECASE)
    return complied


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Logger
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Logger:

    def __init__(self, config: Optional[LoggerConfig] = None) -> None:
        conf = config or LoggerConfig()

        # Thread safety
        self._lock = threading.RLock()

        # Create logger
        self._logger = logging.getLogger(conf.name)
        self._logger.handlers.clear()
        self._logger.propagate = False  # Prevent propagation to parent logger

        # Initialize formatter and handlers
        self._formatter: logging.Formatter | None = None
        self._console_handler: logging.Handler | None = None
        self._file_handler: logging.Handler | None = None

        # Generate default message format if not provided
        message_format = conf.message_format
        if message_format is None:
            tz = "+00:00" if conf.use_utc else conf.timezone_offset
            message_format = (
                '{"timestamp": "%(asctime)s.%(msecs)03d' + tz + '", '
                '"level": "%(levelname)s", '
                '"logger": "%(name)s", '
                '"message": "%(message)s", '
                '"process": %(process)d, '
                '"thread": %(thread)d, '
                '"file": "%(filename)s", '
                '"line": %(lineno)d, '
                '"function": "%(funcName)s"}'
            )

        # Validate backup_suffix format early if file_out is enabled
        if conf.file_out:
            try:
                time.strftime(conf.backup_suffix)
            except (ValueError, KeyError) as exc:
                raise ValueError(f"Invalid backup_suffix format '{conf.backup_suffix}': {exc}") from exc

        # Set formatter and handlers
        self.set_formatter(message_format, conf.datetime_format, conf.use_utc)
        self.set_console_handler(conf.console_out)
        self.set_file_handler(conf.file_out, conf.file_path,
                              conf.backup_suffix, conf.backup_when,
                              conf.backup_interval, conf.backup_count, conf.use_utc)
        self.set_logging_level(conf.level)

    def set_formatter(self, message_format: str, datetime_format: str, use_utc: bool = False):
        with self._lock:
            self._formatter = logging.Formatter(message_format, datetime_format)

            # Use UTC time
            if use_utc:
                self._formatter.converter = time.gmtime

            # Set console handler formatter
            if self._console_handler:
                self._console_handler.setFormatter(self._formatter)

            # Set file handler formatter
            if self._file_handler:
                self._file_handler.setFormatter(self._formatter)

    def set_console_handler(self, console_out: bool):
        with self._lock:
            # With console handler
            if console_out:

                # Create console handler if not exists
                if not self._console_handler:
                    self._console_handler = logging.StreamHandler(sys.stdout)
                    self._console_handler.setFormatter(self._formatter)

                # Register console handler
                if self._console_handler not in self._logger.handlers:
                    self._logger.addHandler(self._console_handler)

            # Without console handler
            else:

                # Unregister console handler
                if self._console_handler and self._console_handler in self._logger.handlers:
                    self._logger.removeHandler(self._console_handler)

    def set_file_handler(self,
                         file_out: bool,
                         file_path: str,
                         backup_suffix: str,
                         backup_when: TimedRotatingWhen = TimedRotatingWhen.MIDNIGHT,
                         backup_interval: int = 1,
                         backup_count: int = 7,
                         use_utc: bool = False):
        with self._lock:
            # With file handler
            if file_out:
                try:
                    # Create directory if not exists
                    base_dir = os.path.dirname(file_path)
                    if base_dir:
                        os.makedirs(base_dir, exist_ok=True)

                    # Validate backup_suffix format
                    try:
                        time.strftime(backup_suffix)
                    except (ValueError, KeyError) as e:
                        raise ValueError(f"Invalid backup_suffix format '{backup_suffix}': {e}") from e

                    # To create file handler if not exists
                    to_create = False
                    if not self._file_handler:
                        to_create = True

                    # To remove file handler if parameters are different
                    else:
                        old_base = os.path.abspath(getattr(self._file_handler, "baseFilename", ""))
                        new_base = os.path.abspath(file_path)
                        old_when = getattr(self._file_handler, "when", None)
                        new_when = str(backup_when).upper()
                        old_interval = getattr(self._file_handler, "interval", None)
                        old_backup = getattr(self._file_handler, "backupCount", None)
                        old_utc = getattr(self._file_handler, "utc", None)
                        if (old_base != new_base or
                            old_when != new_when or
                            old_interval != backup_interval or
                            old_backup != backup_count or
                            old_utc != use_utc):
                            self._logger.removeHandler(self._file_handler)
                            self._file_handler.close()
                            self._file_handler = None
                            to_create = True

                    # Create file handler
                    if to_create:
                        self._file_handler = TimedRotatingFileHandler(filename=file_path,
                                                                      when=str(backup_when),
                                                                      interval=backup_interval,
                                                                      backupCount=backup_count,
                                                                      encoding="utf-8",
                                                                      utc=use_utc,
                                                                      delay=True)

                        # Set suffix
                        self._file_handler.suffix = backup_suffix

                        # Set extMatch to match file suffix
                        self._file_handler.extMatch = _strftime_to_regex(backup_suffix)

                        # Set formatter with UTC setting
                        if self._formatter:
                            # Create new formatter to apply use_utc
                            new_formatter = logging.Formatter(
                                self._formatter._fmt,
                                self._formatter.datefmt
                            )
                            if use_utc:
                                new_formatter.converter = time.gmtime
                            self._file_handler.setFormatter(new_formatter)

                    # Register file handler
                    if self._file_handler not in self._logger.handlers:
                        self._logger.addHandler(self._file_handler)

                except (OSError, IOError) as e:
                    # Fallback: log warning and continue with console only
                    if self._logger.handlers:
                        self._logger.warning(
                            f"Failed to create file handler for '{file_path}': {e}. "
                            f"Falling back to console logging only."
                        )
                    return

            # Without file handler
            else:

                # Unregister file handler
                if self._file_handler and self._file_handler in self._logger.handlers:
                    self._logger.removeHandler(self._file_handler)
                    self._file_handler.close()
                    self._file_handler = None

    def set_logging_level(self, log_level: LoggingLevel):
        with self._lock:
            # Set logger level
            self._logger.setLevel(log_level)

            # Set console handler level
            if self._console_handler and self._console_handler in self._logger.handlers:
                self._console_handler.setLevel(log_level)

            # Set file handler level
            if self._file_handler and self._file_handler in self._logger.handlers:
                self._file_handler.setLevel(log_level)

    def get_logger(self) -> logging.Logger:
        return self._logger

    def get_child(self, suffix: str, propagate: bool = True) -> logging.Logger:
        with self._lock:
            # Create child by name hierarchy
            child_logger = self._logger.getChild(suffix)

            # Configure propagation
            child_logger.propagate = propagate

            # Manually configure child if not propagating
            if not propagate:
                for handler in self._logger.handlers:
                    if handler not in child_logger.handlers:
                        child_logger.addHandler(handler)
                child_logger.setLevel(self._logger.level)

            return child_logger

    def validate_config(self) -> list[str]:
        """Validate logger configuration and return warnings.

        Returns:
            list[str]: List of warning messages. Empty list if no issues found.
        """
        warnings = []

        if not self._logger.handlers:
            warnings.append("No handlers configured. Logs will not be output.")

        if self._file_handler:
            try:
                # Check file write permission
                test_path = getattr(self._file_handler, "baseFilename", "")
                if test_path:
                    test_dir = os.path.dirname(test_path)
                    if test_dir and not os.access(test_dir, os.W_OK):
                        warnings.append(f"No write permission for directory: {test_dir}")
            except Exception as e:
                warnings.append(f"File handler validation failed: {e}")

        return warnings

    # Proxy methods to underlying logger
    def log(self, level, msg, *args, stacklevel=2, **kwargs):
        return self._logger.log(level, msg, *args, stacklevel=stacklevel, **kwargs)

    def debug(self, msg, *args, stacklevel=2, **kwargs):
        return self._logger.debug(msg, *args, stacklevel=stacklevel, **kwargs)

    def info(self, msg, *args, stacklevel=2, **kwargs):
        return self._logger.info(msg, *args, stacklevel=stacklevel, **kwargs)

    def warning(self, msg, *args, stacklevel=2, **kwargs):
        return self._logger.warning(msg, *args, stacklevel=stacklevel, **kwargs)

    def error(self, msg, *args, stacklevel=2, **kwargs):
        return self._logger.error(msg, *args, stacklevel=stacklevel, **kwargs)

    def critical(self, msg, *args, stacklevel=2, **kwargs):
        return self._logger.critical(msg, *args, stacklevel=stacklevel, **kwargs)

    def exception(self, msg, *args, stacklevel=2, **kwargs):
        return self._logger.exception(msg, *args, stacklevel=stacklevel, **kwargs)