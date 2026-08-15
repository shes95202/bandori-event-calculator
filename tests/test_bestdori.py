import pytest

from bandori_event_calculator.bestdori import parse_cutoffs

def test_parse_cutoffs():
    data = {
        "result": True,
        "cutoffs": [
            {
                "ep": 100_000,
                "time": 1000,
            },
            {
                "ep": 200_000,
                "time": 2000,
            },
        ],
    }
    result = parse_cutoffs(data)

    assert len(result) == 2

    assert result[0].score == 100_000
    assert result[0].timestamp_ms == 1000

    assert result[1].score == 200_000
    assert result[1].timestamp_ms == 2000
    
def test_parse_cutoffs_sorts_by_time():
    data = {
        "result": True,
        "cutoffs": [
            {
                "ep": 200_000,
                "time": 2000,
            },
            {
                "ep": 100_000,
                "time": 1000,
            },
        ],
    }

    result = parse_cutoffs(data)

    assert result[0].timestamp_ms == 1000
    assert result[1].timestamp_ms == 2000

def test_parse_cutoffs_rejects_unsuccessful_result():
    data = {
        "result": False,
    }

    with pytest.raises(ValueError):
        parse_cutoffs(data)