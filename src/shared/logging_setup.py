from __future__ import annotations

import logging
import sys

from logging.handlers import RotatingFileHandler
from pathlib import Path

from .time_utilities import utc_dt_to_iso_ts, timestamp_s_to_utc_dt
from .file_io import validate_path_safety, ensure_dir

class UTCISOFormatter(logging.Formatter):
    """
    Formats timestamps
    """

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return utc_dt_to_iso_ts(timestamp_s_to_utc_dt(record.created), timespec="ms")

# ----- ------ ----- ------ ------
# Local utilities
# ----- ------ ----- ------ ------

def _has_stream_handler(root: logging.Logger) -> bool:
    return any(isinstance(h, logging.StreamHandler) for h in root.handlers)

def _file_handler_for_path(root: logging.Logger, log_file: Path) -> logging.FileHandler | None:
    target = str(log_file)
    for h in root.handlers:
        if isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == target:
            return h
    return None


# ----- ------ ----- ------ ------
# Main Function
# ----- ------ ----- ------ ------

def setup_logging(
    *, 
    level: str = "INFO",
    log_file: Path | None = None,
    app_root: Path | None = None, 
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    enable_console: bool = False,
) -> None:
    
    level = getattr(logging, level.upper(), logging.INFO)
    enable_console = bool(enable_console)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    fmt = UTCISOFormatter("%(asctime)s %(levelname)-7s %(name)-8s %(message)s")

    # console

    if enable_console:
        if not _has_stream_handler(root):
            ch = logging.StreamHandler(stream=sys.stderr)
            ch.setLevel(level)
            ch.setFormatter(fmt)
            root.addHandler(ch)
        else: 
            for h in root.handlers:
                if isinstance(h, logging.StreamHandler):
                    h.setLevel(level)
                    h.setFormatter(fmt)

    if log_file is None:
        return
    
    if app_root is not None:
        validate_path_safety(str(log_file), base_dir=str(app_root))

    ensure_dir(str(log_file.parent), base_dir=str(app_root) if app_root else None)

    existing = _file_handler_for_path(root, log_file)
    if existing is not None:
        existing.setLevel(level)
        existing.setFormatter(fmt)
        return
    
    fh = RotatingFileHandler(
        filename=str(log_file), 
        mode="a",
        encoding="utf-8",
        maxBytes=max_bytes,
        backupCount=backup_count,
        delay=False,
    )
    fh.setLevel(level)
    fh.setFormatter(fmt)
    root.addHandler(fh)