from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

AnalysisMode = Literal["full", "harmonic", "percussive"]


@dataclass(frozen=True)
class LevelManifest:
    schema_version: int
    level_id: str
    display_name: str
    audio_file: str
    hit_sound_file: str
    chart_file: str
    audio_offset_seconds: float
    movement_speed: float
    start_position: tuple[float, float]
    initial_direction: tuple[float, float]
    level_directory: Path

    @property
    def audio_path(self) -> Path:
        return self.level_directory / self.audio_file


@dataclass(frozen=True)
class LoadedAudio:
    samples: np.ndarray
    sample_rate: int
    duration_seconds: float


@dataclass(frozen=True)
class AnalyzerConfig:
    analysis_mode: AnalysisMode = "full"
    hop_length: int = 256
    n_fft: int = 2048
    onset_delta: float = 0.07
    minimum_strength: float = 0.15
    minimum_gap_seconds: float = 0.18
    analysis_start_seconds: float | None = None
    analysis_end_seconds: float | None = None
    backtrack: bool = False


@dataclass(frozen=True)
class CandidateNote:
    time_seconds: float
    strength: float
    source_frame: int


@dataclass
class CandidateDiagnostic:
    candidate: CandidateNote
    retained: bool = False
    rejection_reason: str = ""


@dataclass(frozen=True)
class AnalysisResult:
    onset_envelope: np.ndarray
    normalized_envelope: np.ndarray
    raw_candidates: list[CandidateNote]
    after_strength: list[CandidateNote]
    after_range: list[CandidateNote]
    retained_candidates: list[CandidateNote]
    diagnostics: list[CandidateDiagnostic]
