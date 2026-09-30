import json

import pytest

from rhythm_analyzer.serialization import serialize_chart


def test_serialization_is_byte_deterministic():
    payload = {"schemaVersion": 1, "notes": [{"timeSeconds": 1.25}]}
    assert serialize_chart(payload) == serialize_chart(payload)


def test_nan_is_rejected():
    with pytest.raises(ValueError):
        serialize_chart({"value": float("nan")})


def test_serialized_json_ends_with_newline():
    data = serialize_chart({"schemaVersion": 1})
    assert data.endswith(b"\n")
    assert json.loads(data) == {"schemaVersion": 1}
