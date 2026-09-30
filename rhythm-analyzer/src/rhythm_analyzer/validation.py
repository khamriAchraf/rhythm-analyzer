from __future__ import annotations

import math

from .models import AnalyzerConfig, CandidateNote, LevelManifest


class ValidationError(ValueError):
    pass


def validate_config(config: AnalyzerConfig, duration_seconds: float | None = None) -> None:
    if config.analysis_mode not in {"full", "harmonic", "percussive"}:
        raise ValidationError("analysis mode must be full, harmonic, or percussive")
    if config.hop_length <= 0:
        raise ValidationError("hop length must be > 0")
    if config.n_fft <= 0:
        raise ValidationError("n_fft must be > 0")
    if config.onset_delta < 0:
        raise ValidationError("onset delta must be >= 0")
    if not 0 <= config.minimum_strength <= 1:
        raise ValidationError("minimum strength must be in [0, 1]")
    if config.minimum_gap_seconds < 0:
        raise ValidationError("minimum gap must be >= 0")
    if config.analysis_start_seconds is not None and config.analysis_start_seconds < 0:
        raise ValidationError("analysis start must be >= 0")
    if config.analysis_end_seconds is not None:
        if config.analysis_end_seconds < 0:
            raise ValidationError("analysis end must be >= 0")
        if (
            config.analysis_start_seconds is not None
            and config.analysis_end_seconds <= config.analysis_start_seconds
        ):
            raise ValidationError("analysis end must be greater than analysis start")
    if duration_seconds is not None:
        if (
            config.analysis_start_seconds is not None
            and config.analysis_start_seconds > duration_seconds
        ):
            raise ValidationError("analysis start exceeds audio duration")


def validate_chart(
    manifest: LevelManifest,
    duration_seconds: float,
    notes: list[CandidateNote],
    minimum_gap_seconds: float,
) -> None:
    if not notes:
        raise ValidationError("No playable notes remain after filtering")

    previous_time: float | None = None
    for index, note in enumerate(notes):
        if not math.isfinite(note.time_seconds) or note.time_seconds < 0:
            raise ValidationError(f"notes[{index}].timeSeconds is invalid")
        rounded_time = round(note.time_seconds, 6)
        if rounded_time > round(duration_seconds, 6) + 1e-6:
            raise ValidationError(f"notes[{index}].timeSeconds exceeds audio duration")
        if not math.isfinite(note.strength) or not 0 <= note.strength <= 1:
            raise ValidationError(f"notes[{index}].strength must be in [0, 1]")
        if note.source_frame < 0:
            raise ValidationError(f"notes[{index}].sourceFrame must be >= 0")

        if previous_time is not None:
            if rounded_time <= previous_time:
                raise ValidationError("Rounding creates duplicate or unsorted note timestamps")
            if rounded_time - previous_time < minimum_gap_seconds - 1e-6:
                raise ValidationError("Minimum-gap rule was violated after serialization rounding")
        previous_time = rounded_time

    if round(notes[0].time_seconds, 6) + manifest.audio_offset_seconds < 0:
        raise ValidationError("First effective note time is negative after audio offset")
