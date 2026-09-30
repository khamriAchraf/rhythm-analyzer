from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audio import load_audio, sha256_file
from .diagnostics import write_candidate_csv, write_marker_plot
from .manifest import load_manifest
from .models import AnalyzerConfig
from .onset import compute_onset_candidates
from .serialization import build_chart_payload, write_chart_atomic
from .validation import validate_chart, validate_config


class CliError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rhythm-analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze one level directory")
    analyze.add_argument("--level-dir", required=True, type=Path)
    analyze.add_argument("--output", default="notes.generated.json")
    analyze.add_argument(
        "--analysis-mode", choices=["full", "harmonic", "percussive"], default="full"
    )
    analyze.add_argument("--hop-length", type=int, default=256)
    analyze.add_argument("--n-fft", type=int, default=2048)
    analyze.add_argument("--onset-delta", type=float, default=0.07)
    analyze.add_argument("--minimum-strength", type=float, default=0.15)
    analyze.add_argument("--minimum-gap", type=float, default=0.18)
    analyze.add_argument("--analysis-start", type=float)
    analyze.add_argument("--analysis-end", type=float)
    analyze.add_argument("--backtrack", action="store_true")
    analyze.add_argument("--diagnostics", action="store_true")
    analyze.add_argument("--force", action="store_true")
    analyze.add_argument(
        "--allow-approved-chart-overwrite",
        action="store_true",
        help="Required in addition to --force when output is notes.json",
    )
    return parser


def _config_from_args(args: argparse.Namespace) -> AnalyzerConfig:
    return AnalyzerConfig(
        analysis_mode=args.analysis_mode,
        hop_length=args.hop_length,
        n_fft=args.n_fft,
        onset_delta=args.onset_delta,
        minimum_strength=args.minimum_strength,
        minimum_gap_seconds=args.minimum_gap,
        analysis_start_seconds=args.analysis_start,
        analysis_end_seconds=args.analysis_end,
        backtrack=args.backtrack,
    )


def run_analyze(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.level_dir)
    config = _config_from_args(args)
    validate_config(config)

    output_path = manifest.level_directory / args.output
    if output_path.name == "notes.json" and not (
        args.force and args.allow_approved_chart_overwrite
    ):
        raise CliError(
            "Refusing to overwrite notes.json. Use --force and "
            "--allow-approved-chart-overwrite explicitly."
        )
    if output_path.exists() and not args.force:
        raise CliError(f"Output already exists: {output_path}. Use --force to replace it.")

    audio_hash = sha256_file(manifest.audio_path)
    audio = load_audio(manifest.audio_path)
    validate_config(config, audio.duration_seconds)
    result = compute_onset_candidates(audio, config)
    validate_chart(
        manifest,
        audio.duration_seconds,
        result.retained_candidates,
        config.minimum_gap_seconds,
    )

    payload = build_chart_payload(
        manifest,
        audio_hash,
        audio.duration_seconds,
        audio.sample_rate,
        config,
        result.retained_candidates,
    )
    write_chart_atomic(payload, output_path)

    diagnostics_path: Path | None = None
    if args.diagnostics:
        diagnostics_dir = manifest.level_directory / "diagnostics"
        diagnostics_path = diagnostics_dir / "onset-markers.png"
        write_candidate_csv(result, diagnostics_dir / "candidates.csv")
        write_marker_plot(audio, result, config.hop_length, diagnostics_path)

    print(f"Level: {manifest.level_id}")
    print(f"Audio: {manifest.audio_file}")
    print(f"Duration: {audio.duration_seconds:.3f} s")
    print(f"Sample rate: {audio.sample_rate} Hz")
    print(f"Raw candidates: {len(result.raw_candidates)}")
    print(f"After strength filter: {len(result.after_strength)}")
    print(f"After analysis range: {len(result.after_range)}")
    print(f"After minimum-gap merge: {len(result.retained_candidates)}")
    print(f"Output: {output_path.name}")
    if diagnostics_path is not None:
        print(f"Diagnostics: {diagnostics_path.relative_to(manifest.level_directory)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            return run_analyze(args)
        parser.error(f"Unsupported command: {args.command}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
