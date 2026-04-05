from dataclasses import dataclass
from pathlib import Path
import json

_GLOBAL_LOGLEVEL: str | None = None
_GLOBAL_CONFIG_PATH: Path | None = None

@dataclass(frozen=True)
class Settings:
    log_level: str
    config_path: Path

def read_json(path: Path) -> dict:
    with path.expanduser().open("r", encoding="utf-8-sig") as f:
        return json.load(f)

def resolve_settings(*, cli_log_level: str | None, cli_config: Path) -> Settings:
    log_level = cli_log_level or "INFO"
    config_path = cli_config

    if _GLOBAL_CONFIG_PATH is not None:
        config_path = _GLOBAL_CONFIG_PATH
    if _GLOBAL_LOGLEVEL is not None:
        log_level = _GLOBAL_LOGLEVEL

    return Settings(log_level=log_level, config_path=config_path)