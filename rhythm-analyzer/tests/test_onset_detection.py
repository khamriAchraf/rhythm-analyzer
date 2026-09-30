import numpy as np
import soundfile as sf

from rhythm_analyzer.audio import load_audio
from rhythm_analyzer.models import AnalyzerConfig
from rhythm_analyzer.onset import compute_onset_candidates


def test_synthetic_clicks_are_detected_near_expected_times(tmp_path):
    sr = 22050
    duration = 2.2
    samples = np.zeros(int(sr * duration), dtype=np.float32)
    expected = [0.50, 1.00, 1.75]

    # Short Hann-windowed noise bursts are easier for spectral onset detection
    # than ideal single-sample impulses and still form deterministic transients.
    rng = np.random.default_rng(12345)
    burst_len = 256
    window = np.hanning(burst_len).astype(np.float32)
    for time_seconds in expected:
        start = int(time_seconds * sr)
        burst = rng.standard_normal(burst_len).astype(np.float32) * window
        samples[start : start + burst_len] += burst

    path = tmp_path / "clicks.wav"
    sf.write(path, samples, sr, subtype="FLOAT")

    audio = load_audio(path)
    config = AnalyzerConfig(
        hop_length=128,
        n_fft=1024,
        onset_delta=0.05,
        minimum_strength=0.05,
        minimum_gap_seconds=0.15,
    )
    result = compute_onset_candidates(audio, config)

    tolerance = 2 * config.hop_length / sr
    actual = [candidate.time_seconds for candidate in result.retained_candidates]
    for expected_time in expected:
        assert any(abs(value - expected_time) <= tolerance for value in actual), (
            expected_time,
            actual,
        )
