from rhythm_analyzer.filtering import filter_by_range
from rhythm_analyzer.models import CandidateNote


def test_analysis_range_preserves_absolute_time_origin():
    candidates = [
        CandidateNote(9.9, 1.0, 1),
        CandidateNote(10.2, 1.0, 2),
        CandidateNote(19.8, 1.0, 3),
        CandidateNote(20.1, 1.0, 4),
    ]
    retained = filter_by_range(candidates, 10.0, 20.0)
    assert [candidate.time_seconds for candidate in retained] == [10.2, 19.8]
