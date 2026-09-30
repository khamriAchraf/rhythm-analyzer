from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import librosa

from . import __version__
from .models import AnalyzerConfig, CandidateNote, LevelManifest


def build_chart_payload(
    manifest: LevelManifest,
    audio_sha256: str,
    duration_seconds: float,
    sample_rate: int,
    config: AnalyzerConfig,
    notes: list[CandidateNote],
) -> dict:
    return {
        "schemaVersion": 1,
        "levelId": manifest.level_id,
        "audioFile": manifest.audio_file,
        "audioSha256": audio_sha256,
        "durationSeconds": round(duration_seconds, 6),
        "sourceSampleRate": int(sample_rate),
        "generator": {
            "name": "librosa-onset",
            "implementationVersion": __version__,
            "librosaVersion": librosa.__version__,
            "analysisMode": config.analysis_mode,
            "hopLength": config.hop_length,
            "nFft": config.n_fft,
            "onsetDelta": config.onset_delta,
            "minimumGapSeconds": config.minimum_gap_seconds,
            "minimumNormalizedStrength": config.minimum_strength,
            "analysisStartSeconds": config.analysis_start_seconds,
            "analysisEndSeconds": config.analysis_end_seconds,
            "backtrack": config.backtrack,
        },
        "notes": [
            {
                "timeSeconds": round(note.time_seconds, 6),
                "strength": round(note.strength, 6),
                "sourceFrame": note.source_frame,
            }
            for note in notes
        ],
    }


def serialize_chart(payload: dict) -> bytes:
    text = json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    return text.encode("utf-8")


def write_chart_atomic(payload: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = serialize_chart(payload)

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
