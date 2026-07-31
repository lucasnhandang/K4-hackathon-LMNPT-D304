from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    pass


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"Dòng {line_number} trong .env không có dấu '='.")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _required(values: dict[str, str], key: str) -> str:
    value = values.get(key, "").strip()
    if not value or "replace_with" in value.casefold():
        raise ConfigError(f"Thiếu cấu hình {key}.")
    return value


def _snowflake(value: str, key: str) -> int:
    if not value.isdigit() or not 17 <= len(value) <= 20:
        raise ConfigError(f"{key} phải là Discord ID gồm 17–20 chữ số.")
    return int(value)


def _snowflake_set(values: dict[str, str], key: str) -> frozenset[int]:
    raw = _required(values, key)
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise ConfigError(f"{key} không được rỗng.")
    result = frozenset(_snowflake(part, key) for part in parts)
    if len(result) != len(parts):
        raise ConfigError(f"{key} chứa ID trùng nhau.")
    return result


def _bool_value(values: dict[str, str], key: str, default: bool) -> bool:
    raw = values.get(key)
    if raw is None:
        return default
    normalized = raw.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{key} phải là true hoặc false.")


def _int_value(
    values: dict[str, str],
    key: str,
    default: int,
    minimum: int,
) -> int:
    raw = values.get(key)
    if raw is None or not raw.strip():
        return default
    try:
        result = int(raw)
    except ValueError as error:
        raise ConfigError(f"{key} phải là số nguyên.") from error
    if result < minimum:
        raise ConfigError(f"{key} phải lớn hơn hoặc bằng {minimum}.")
    return result


@dataclass(frozen=True)
class CollectorConfig:
    token: str
    guild_id: int
    official_channel_ids: frozenset[int]
    community_channel_ids: frozenset[int]
    command_channel_ids: frozenset[int]
    collect_channel_ids: frozenset[int]
    pseudonym_secret: str
    database_path: Path
    backfill_on_start: bool
    backfill_limit_per_channel: int | None
    retention_days: int

    def tier_for(self, channel_id: int, parent_channel_id: int | None = None) -> str | None:
        candidates = {channel_id}
        if parent_channel_id is not None:
            candidates.add(parent_channel_id)
        if candidates & self.official_channel_ids:
            return "official"
        if candidates & self.community_channel_ids:
            return "community"
        if candidates & self.command_channel_ids:
            return "command"
        return None


def load_config(env_path: str | Path = ".env") -> CollectorConfig:
    path = Path(env_path).resolve()
    if not path.exists():
        raise ConfigError(f"Không tìm thấy file cấu hình: {path}")
    values = _read_env(path)

    official = _snowflake_set(values, "OFFICIAL_SOURCE_CHANNEL_IDS")
    community = _snowflake_set(values, "COMMUNITY_CHANNEL_IDS")
    command = _snowflake_set(values, "COMMAND_CHANNEL_IDS")
    collect = _snowflake_set(values, "COLLECT_CHANNEL_IDS")

    groups = [official, community, command]
    for index, left in enumerate(groups):
        for right in groups[index + 1 :]:
            overlap = left & right
            if overlap:
                raise ConfigError("Một channel ID không được nằm trong nhiều nhóm tin cậy.")

    expected_collect = official | community | command
    if collect != expected_collect:
        raise ConfigError(
            "COLLECT_CHANNEL_IDS phải bằng đúng hợp của OFFICIAL, COMMUNITY và COMMAND."
        )
    if len(collect) != 7:
        raise ConfigError("Prototype yêu cầu đúng 7 channel được phép thu thập.")

    secret = _required(values, "PSEUDONYM_SECRET")
    if len(secret) < 32:
        raise ConfigError("PSEUDONYM_SECRET phải dài ít nhất 32 ký tự.")

    raw_limit = _int_value(values, "BACKFILL_LIMIT_PER_CHANNEL", 0, 0)
    database_value = values.get("DATABASE_PATH", "runtime/discord_messages.sqlite3")
    database_path = Path(database_value)
    if not database_path.is_absolute():
        database_path = path.parent / database_path

    return CollectorConfig(
        token=_required(values, "DISCORD_TOKEN"),
        guild_id=_snowflake(_required(values, "DISCORD_GUILD_ID"), "DISCORD_GUILD_ID"),
        official_channel_ids=official,
        community_channel_ids=community,
        command_channel_ids=command,
        collect_channel_ids=collect,
        pseudonym_secret=secret,
        database_path=database_path.resolve(),
        backfill_on_start=_bool_value(values, "BACKFILL_ON_START", True),
        backfill_limit_per_channel=None if raw_limit == 0 else raw_limit,
        retention_days=_int_value(values, "DATA_RETENTION_DAYS", 30, 1),
    )
