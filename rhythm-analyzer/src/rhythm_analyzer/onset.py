from __future__ import annotations

import librosa
import numpy as np

from .filtering import filter_by_range, filter_by_strength, merge_close_candidates
from .models import (
    AnalysisResult,
    AnalyzerConfig,
    CandidateDiagnostic,
    CandidateNote,
    LoadedAudio,
)


class OnsetAnalysisError(RuntimeError):
    pass


def select_analysis_signal(y: np.ndarray, mode: str) -> np.ndarray:
    if mode == "full":
        return y
    if mode not in {"harmonic", "percussive"}:
        raise OnsetAnalysisError(f"Unsupported analysis mode: {mode}")
    harmonic, percussive = librosa.effects.hpss(y)
    return harmonic if mode == "harmonic" else percussive


def compute_onset_candidates(
    audio: LoadedAudio, config: AnalyzerConfig
) -> AnalysisResult:
    analysis_y = select_analysis_signal(audio.samples, config.analysis_mode)

    onset_envelope = librosa.onset.onset_strength(
        y=analysis_y,
        sr=audio.sample_rate,
        hop_length=config.hop_length,
        n_fft=config.n_fft,
    )
    maximum = float(np.max(onset_envelope, initial=0.0))
    if maximum <= 0.0:
        raise OnsetAnalysisError("No onset energy was detected")
    normalized = onset_envelope / maximum

    frames = librosa.onset.onset_detect(
        onset_envelope=onset_envelope,
        sr=audio.sample_rate,
        hop_length=config.hop_length,
        units="frames",
        backtrack=config.backtrack,
        delta=config.onset_delta,
    )
    times = librosa.frames_to_time(
        frames, sr=audio.sample_rate, hop_length=config.hop_length
    )

    raw: list[CandidateNote] = []
    for frame, time_seconds in zip(frames, times, strict=True):
        frame_int = int(frame)
        raw.append(
            CandidateNote(
                time_seconds=float(time_seconds),
                strength=float(normalized[frame_int]),
                source_frame=frame_int,
            )
        )

    after_strength = filter_by_strength(raw, config.minimum_strength)
    after_range = filter_by_range(
        after_strength,
        config.analysis_start_seconds,
        config.analysis_end_seconds,
    )
    retained = merge_close_candidates(after_range, config.minimum_gap_seconds)

    retained_keys = {(c.source_frame, c.time_seconds) for c in retained}
    after_strength_keys = {(c.source_frame, c.time_seconds) for c in after_strength}
    after_range_keys = {(c.source_frame, c.time_seconds) for c in after_range}

    diagnostics: list[CandidateDiagnostic] = []
    for candidate in raw:
        key = (candidate.source_frame, candidate.time_seconds)
        if key in retained_keys:
            diagnostics.append(CandidateDiagnostic(candidate, True, ""))
        elif key not in after_strength_keys:
            diagnostics.append(
                CandidateDiagnostic(candidate, False, "below_strength_threshold")
            )
        elif key not in after_range_keys:
            diagnostics.append(
                CandidateDiagnostic(candidate, False, "outside_analysis_range")
            )
        else:
            diagnostics.append(
                CandidateDiagnostic(candidate, False, "merged_with_stronger_candidate")
            )

    return AnalysisResult(
        onset_envelope=onset_envelope,
        normalized_envelope=normalized,
        raw_candidates=raw,
        after_strength=after_strength,
        after_range=after_range,
        retained_candidates=retained,
        diagnostics=diagnostics,
    )
