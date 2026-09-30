from __future__ import annotations

import csv
from pathlib import Path

import librosa
import matplotlib.pyplot as plt
import numpy as np

from .models import AnalysisResult, LoadedAudio


def write_candidate_csv(result: AnalysisResult, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "index",
                "time_seconds",
                "strength",
                "source_frame",
                "retained",
                "rejection_reason",
            ]
        )
        for index, diagnostic in enumerate(result.diagnostics):
            candidate = diagnostic.candidate
            writer.writerow(
                [
                    index,
                    f"{candidate.time_seconds:.6f}",
                    f"{candidate.strength:.6f}",
                    candidate.source_frame,
                    str(diagnostic.retained).lower(),
                    diagnostic.rejection_reason,
                ]
            )


def write_marker_plot(
    audio: LoadedAudio,
    result: AnalysisResult,
    hop_length: int,
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    waveform_times = np.arange(len(audio.samples), dtype=float) / audio.sample_rate
    envelope_times = librosa.frames_to_time(
        np.arange(len(result.normalized_envelope)),
        sr=audio.sample_rate,
        hop_length=hop_length,
    )

    fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
    axes[0].plot(waveform_times, audio.samples, linewidth=0.5)
    axes[0].set_ylabel("Amplitude")
    axes[0].set_title("Waveform and onset candidates")

    axes[1].plot(envelope_times, result.normalized_envelope, linewidth=1.0)
    axes[1].set_ylabel("Normalized onset strength")
    axes[1].set_xlabel("Time (seconds)")
    axes[1].set_ylim(0.0, 1.05)

    retained_frames = {candidate.source_frame for candidate in result.retained_candidates}
    for candidate in result.raw_candidates:
        retained = candidate.source_frame in retained_frames
        for axis in axes:
            axis.axvline(
                candidate.time_seconds,
                alpha=0.85 if retained else 0.18,
                linewidth=1.2 if retained else 0.8,
            )

    for index, candidate in enumerate(result.retained_candidates):
        axes[1].annotate(
            str(index),
            (candidate.time_seconds, candidate.strength),
            xytext=(2, 4),
            textcoords="offset points",
            fontsize=7,
        )

    axes[1].set_xlim(0.0, audio.duration_seconds)
    fig.tight_layout()
    fig.savefig(destination, dpi=160)
    plt.close(fig)
