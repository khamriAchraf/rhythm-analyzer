from __future__ import annotations

import hashlib
import math
from pathlib import Path

import librosa
import numpy as np

from .models import LoadedAudio


class AudioAnalysisError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_audio(path: Path) -> LoadedAudio:
    try:
        y, sr = librosa.load(path, sr=None, mono=True)
    except Exception as exc:
        raise AudioAnalysisError(f"Could not decode audio: {exc}") from exc

    if sr <= 0:
        raise AudioAnalysisError("Decoded audio has an invalid sample rate")
    if y.size == 0:
        raise AudioAnalysisError("Decoded audio is empty")
    if not np.isfinite(y).all():
        raise AudioAnalysisError("Decoded audio contains non-finite samples")

    duration = float(len(y) / sr)
    if not math.isfinite(duration) or duration <= 0:
        raise AudioAnalysisError("Decoded audio has an invalid duration")

    return LoadedAudio(samples=y, sample_rate=int(sr), duration_seconds=duration)
