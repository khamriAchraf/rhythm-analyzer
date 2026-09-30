from __future__ import annotations

from .models import CandidateNote


def filter_by_strength(
    candidates: list[CandidateNote], threshold: float
) -> list[CandidateNote]:
    return [candidate for candidate in candidates if candidate.strength >= threshold]


def filter_by_range(
    candidates: list[CandidateNote],
    start_seconds: float | None,
    end_seconds: float | None,
) -> list[CandidateNote]:
    return [
        candidate
        for candidate in candidates
        if (start_seconds is None or candidate.time_seconds >= start_seconds)
        and (end_seconds is None or candidate.time_seconds <= end_seconds)
    ]


def merge_close_candidates(
    candidates: list[CandidateNote], minimum_gap_seconds: float
) -> list[CandidateNote]:
    if not candidates:
        return []

    ordered = sorted(candidates, key=lambda candidate: candidate.time_seconds)
    clusters: list[list[CandidateNote]] = [[ordered[0]]]

    for candidate in ordered[1:]:
        if (
            candidate.time_seconds - clusters[-1][-1].time_seconds
            < minimum_gap_seconds - 1e-12
        ):
            clusters[-1].append(candidate)
        else:
            clusters.append([candidate])

    retained: list[CandidateNote] = []
    for cluster in clusters:
        # max strength; equal strength resolves to the earlier candidate.
        best = max(cluster, key=lambda c: (c.strength, -c.time_seconds))
        retained.append(best)

    return sorted(retained, key=lambda candidate: candidate.time_seconds)
