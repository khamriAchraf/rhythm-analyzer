from rhythm_analyzer.filtering import filter_by_strength, merge_close_candidates
from rhythm_analyzer.models import CandidateNote


def note(time: float, strength: float, frame: int) -> CandidateNote:
    return CandidateNote(time, strength, frame)


def test_strength_threshold_is_inclusive():
    candidates = [note(1.0, 0.14, 1), note(2.0, 0.15, 2)]
    assert filter_by_strength(candidates, 0.15) == [candidates[1]]


def test_strongest_candidate_wins_close_cluster():
    candidates = [note(1.0, 0.4, 1), note(1.1, 0.9, 2), note(1.2, 0.7, 3)]
    assert merge_close_candidates(candidates, 0.18) == [candidates[1]]


def test_equal_strength_tie_keeps_earlier_candidate():
    candidates = [note(1.0, 0.8, 1), note(1.1, 0.8, 2)]
    assert merge_close_candidates(candidates, 0.18) == [candidates[0]]


def test_exact_minimum_gap_keeps_both():
    candidates = [note(1.0, 0.8, 1), note(1.18, 0.9, 2)]
    assert merge_close_candidates(candidates, 0.18) == candidates
