# Rhythm Analyzer

Offline Librosa onset analyzer for the Unity rhythm game level contract.

## Install

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

python -m pip install -e ".[dev]"
```

## Expected level folder

```text
Levels/zenzenzense_40s/
├── level.json
├── audio.wav
├── hit.wav
└── notes.json              # optional approved/manual chart
```

`level.json` must follow the schema agreed in the handoff. The folder name must equal its `id`.

## Analyze

```bash
rhythm-analyzer analyze \
  --level-dir ./Levels/zenzenzense_40s \
  --output notes.generated.json \
  --analysis-mode full \
  --hop-length 256 \
  --n-fft 2048 \
  --onset-delta 0.07 \
  --minimum-strength 0.15 \
  --minimum-gap 0.18 \
  --diagnostics
```

Equivalent module invocation:

```bash
python -m rhythm_analyzer analyze --level-dir ./Levels/zenzenzense_40s --diagnostics
```

If `notes.generated.json` already exists, add `--force`.

The CLI deliberately refuses to overwrite `notes.json` unless **both** flags are supplied:

```bash
--force --allow-approved-chart-overwrite
```

## Outputs

```text
notes.generated.json
diagnostics/candidates.csv
diagnostics/onset-markers.png
```

The JSON keeps the original audio time origin. Analysis ranges only filter events; they never shift timestamps.

## Test

```bash
pytest -q
```

The included tests cover contract validation, filtering/merging behavior, deterministic serialization, absolute timeline filtering, and a real Librosa run over deterministic synthetic transients.

## Useful tuning order

Start with the defaults and inspect `diagnostics/onset-markers.png`. Then tune in this order:

1. `--analysis-mode full|harmonic|percussive`
2. `--onset-delta`
3. `--minimum-strength`
4. `--minimum-gap`

Avoid tuning from JSON alone. The generated chart is a candidate chart, not guaranteed melody transcription.
