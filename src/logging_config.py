"""Logging configuration with daily rotating files.

Levels (from least to most verbose):
    ERROR   → only errors
    WARNING → errors + warnings
    INFO    → normal operation (default)
    DEBUG   → detailed debugging info
    VERBOSE → everything, including library internals

Configure via .env:
    LOG_LEVEL=DEBUG
    LOG_DIR=logs
"""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import config

# Custom VERBOSE level (below DEBUG)
VERBOSE = 5
logging.addLevelName(VERBOSE, "VERBOSE")


def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE):
        self._log(VERBOSE, message, args, **kwargs)


logging.Logger.verbose = verbose

# Map string names to levels
LEVEL_MAP = {
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "VERBOSE": VERBOSE,
}


def setup_logging():
    """Configure root logger with console + rotating file handlers."""
    level_name = config.LOG_LEVEL.upper()
    level = LEVEL_MAP.get(level_name, logging.INFO)

    log_dir = Path(config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    root = logging.getLogger()
    root.setLevel(level)

    # Clear existing handlers (avoid duplicates on restart)
    root.handlers.clear()

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Daily rotating file handler
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "mock_trader.log",
        when="midnight",
        interval=1,
        backupCount=30,  # keep 30 days
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"
    root.addHandler(file_handler)

    # Error-only file (always captures errors regardless of level)
    error_handler = TimedRotatingFileHandler(
        filename=log_dir / "errors.log",
        when="midnight",
        interval=1,
        backupCount=90,  # keep 90 days
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root.addHandler(error_handler)

    # Quiet noisy libraries unless VERBOSE
    if level > VERBOSE:
        for lib in ["urllib3", "requests", "psycopg2"]:
            logging.getLogger(lib).setLevel(logging.WARNING)

    logging.info("Logging initialized: level=%s, dir=%s", level_name, log_dir)
