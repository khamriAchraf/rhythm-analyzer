from __future__ import annotations

import json
import math
import re
from pathlib import Path

from .models import LevelManifest

LEVEL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")


class ManifestError(ValueError):
    pass


def _finite_number(value: object, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ManifestError(f"{field} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ManifestError(f"{field} must be finite")
    return result


def _vector2(value: object, field: str) -> tuple[float, float]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field} must be an object with x and y")
    return (
        _finite_number(value.get("x"), f"{field}.x"),
        _finite_number(value.get("y"), f"{field}.y"),
    )


def load_manifest(level_directory: Path) -> LevelManifest:
    level_directory = level_directory.resolve()
    manifest_path = level_directory / "level.json"
    if not manifest_path.is_file():
        raise ManifestError(f"Missing manifest: {manifest_path}")

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"Could not read level.json: {exc}") from exc

    if data.get("schemaVersion") != 1:
        raise ManifestError("level.json schemaVersion must equal 1")

    level_id = data.get("id")
    if not isinstance(level_id, str) or not LEVEL_ID_RE.fullmatch(level_id):
        raise ManifestError("id must match ^[a-z0-9][a-z0-9_]*$")
    if level_id != level_directory.name:
        raise ManifestError(
            f"Level id '{level_id}' must match directory name '{level_directory.name}'"
        )

    def required_string(name: str) -> str:
        value = data.get(name)
        if not isinstance(value, str) or not value:
            raise ManifestError(f"{name} must be a non-empty string")
        return value

    audio_file = required_string("audioFile")
    audio_path = level_directory / audio_file
    if not audio_path.is_file():
        raise ManifestError(f"Missing audio file: {audio_path}")

    movement_speed = _finite_number(data.get("movementSpeed"), "movementSpeed")
    if movement_speed <= 0:
        raise ManifestError("movementSpeed must be > 0")

    initial_direction = _vector2(data.get("initialDirection"), "initialDirection")
    if initial_direction == (0.0, 0.0):
        raise ManifestError("initialDirection must not be (0, 0)")

    return LevelManifest(
        schema_version=1,
        level_id=level_id,
        display_name=required_string("displayName"),
        audio_file=audio_file,
        hit_sound_file=required_string("hitSoundFile"),
        chart_file=required_string("chartFile"),
        audio_offset_seconds=_finite_number(
            data.get("audioOffsetSeconds", 0.0), "audioOffsetSeconds"
        ),
        movement_speed=movement_speed,
        start_position=_vector2(data.get("startPosition"), "startPosition"),
        initial_direction=initial_direction,
        level_directory=level_directory,
    )
