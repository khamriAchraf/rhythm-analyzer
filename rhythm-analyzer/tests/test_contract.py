import json
from pathlib import Path

import pytest

from rhythm_analyzer.manifest import ManifestError, load_manifest


def write_manifest(level_dir: Path, **overrides):
    data = {
        "schemaVersion": 1,
        "id": level_dir.name,
        "displayName": "Test",
        "audioFile": "audio.wav",
        "hitSoundFile": "hit.wav",
        "chartFile": "notes.json",
        "audioOffsetSeconds": 0.0,
        "movementSpeed": 5.0,
        "startPosition": {"x": 0.0, "y": 0.0},
        "initialDirection": {"x": 1.0, "y": 1.0},
    }
    data.update(overrides)
    (level_dir / "level.json").write_text(json.dumps(data), encoding="utf-8")
    (level_dir / "audio.wav").write_bytes(b"placeholder")


def test_valid_manifest_loads(tmp_path):
    level_dir = tmp_path / "test_level"
    level_dir.mkdir()
    write_manifest(level_dir)
    assert load_manifest(level_dir).level_id == "test_level"


def test_unsupported_schema_fails(tmp_path):
    level_dir = tmp_path / "test_level"
    level_dir.mkdir()
    write_manifest(level_dir, schemaVersion=2)
    with pytest.raises(ManifestError):
        load_manifest(level_dir)


def test_invalid_level_id_fails(tmp_path):
    level_dir = tmp_path / "test_level"
    level_dir.mkdir()
    write_manifest(level_dir, id="Bad-ID")
    with pytest.raises(ManifestError):
        load_manifest(level_dir)
