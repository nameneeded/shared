from __future__ import annotations

import time

from datetime import datetime, timezone
from typing import Literal

ISOGRANULARITY = Literal["s", "ms", "msc"]

# --- datetime objects ---
def utc_now_dt() -> datetime:
    """Returns current UTC datetime"""
    return datetime.now(tz=timezone.utc)

def pathsafe_ts_to_utc_dt(string: str) -> datetime: 
    """Parse a pathsafe ts (yyyy-mm-ddThh-mm-ssZ) to utc dt"""
    return datetime.strptime(string, "%Y-%m-%dT%H-%M-%SZ").replace(tzinfo=timezone.utc)

def iso_ts_to_utc_dt(string: str) -> datetime:
    """Parse an ISO ts (yyyy-mm-ddThh:mm:ssZ) to utc dt"""
    return datetime.strptime(string, "%Y-%m-%dT%H-%M-%SZ").replace(tzinfo=timezone.utc)

# --- datetime ts strings ---
def utc_dt_to_pathsafe_ts(dt: datetime) -> str:
    """Convert a UTC dt to a pathsafe ts (yyyy-mm-ddThh-mm-ssZ)"""
    return dt.strftime("%Y-%m-%dT%H-%M-%SZ")

def utc_dt_to_iso_ts(dt: datetime, timespec: ISOGRANULARITY = "s") -> str:
    """
    Convert a UTC dt to ISO format with 'Z' (yyyy-mm-ddThh:mm:ssZ)

    timespec: 
        - "s": second precision             yyyy-mm-ddThh:mm:ssZ (default)
        - "ms": millisecond precision       yyyy-mm-ddThh:mm:ss.SSSZ
        - "msc": microsecond precision      yyyy-mm-ddThh:mm:ss.SSSSSSZ
    """

    if timespec =="s":
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif timespec =="ms":
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    elif timespec =="msc":
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    else: 
        raise ValueError(f"Invalid timespec: {timespec}")
    
def iso_ts_to_pathsafe_ts(string: str) -> str:
    """Convert an ISO ts with 'Z' to a pathsafe ts."""
    dt = iso_ts_to_utc_dt(string)
    return utc_dt_to_pathsafe_ts(dt)

# --- POSIX timestamp functions ---
def timestamp_s_to_utc_dt(ts_s: float) -> datetime:
    """Convert a POSIX timestamp (seconds since epoch) to a UTC dt"""
    return datetime.fromtimestamp(ts_s, tz=timezone.utc)

def utc_dt_to_timestamp_s(dt: datetime) -> float:
    """Convert a utc dt to a timestamp(seconds)"""
    pass

# --- Performance Timing Utilities
def perf_counter_s() -> float:
    """Monotonic clock for durations in seconds."""
    return time.perf_counter()

def elapsed_ms(start_perf_s: float, end_perf_s: float) -> int:
    """Return elapsed miliseconds between the given start and end times"""
    return int((end_perf_s - start_perf_s) * 1000)
