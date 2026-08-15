import pytest

from bandori_event_calculator.bestdori import (
    Server,
    find_current_event,
    parse_cutoffs,
    parse_events,
)

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
        
def test_parse_events_for_jp():
    data = {
        "100": {
            "eventName": [
                "JP Event",
                None,
                "TW Event",
                None,
                None,
            ],
            "eventType": "mission_live",
            "startAt": [
                "1000",
                None,
                "3000",
                None,
                None,
            ],
            "endAt": [
                "2000",
                None,
                "4000",
                None,
                None,
            ],
        },
    }

    result = parse_events(
        data=data,
        server=Server.JP,
    )

    assert len(result) == 1

    event = result[0]

    assert event.id == 100
    assert event.server == Server.JP
    assert event.name == "JP Event"
    assert event.event_type == "mission_live"
    assert event.start_at_ms == 1000
    assert event.end_at_ms == 2000
    
def test_parse_events_for_tw():
    data = {
        "100": {
            "eventName": [
                "JP Event",
                None,
                "TW Event",
                None,
                None,
            ],
            "eventType": "mission_live",
            "startAt": [
                "1000",
                None,
                "3000",
                None,
                None,
            ],
            "endAt": [
                "2000",
                None,
                "4000",
                None,
                None,
            ],
        },
    }

    result = parse_events(
        data=data,
        server=Server.TW,
    )

    assert len(result) == 1

    event = result[0]

    assert event.server == Server.TW
    assert event.name == "TW Event"
    assert event.start_at_ms == 3000
    assert event.end_at_ms == 4000

def test_find_current_event():
    data = {
        "100": {
            "eventName": [
                "Old Event",
                None,
                None,
                None,
                None,
            ],
            "eventType": "mission_live",
            "startAt": [
                "1000",
                None,
                None,
                None,
                None,
            ],
            "endAt": [
                "2000",
                None,
                None,
                None,
                None,
            ],
        },
        "101": {
            "eventName": [
                "Current Event",
                None,
                None,
                None,
                None,
            ],
            "eventType": "challenge",
            "startAt": [
                "3000",
                None,
                None,
                None,
                None,
            ],
            "endAt": [
                "5000",
                None,
                None,
                None,
                None,
            ],
        },
    }

    result = find_current_event(
        data=data,
        server=Server.JP,
        now_ms=4000,
    )

    assert result is not None
    assert result.id == 101
    assert result.name == "Current Event"

def test_find_current_event_returns_none_when_inactive():
    data = {
        "100": {
            "eventName": [
                None,
                None,
                "TW Event",
                None,
                None,
            ],
            "eventType": "mission_live",
            "startAt": [
                None,
                None,
                "1000",
                None,
                None,
            ],
            "endAt": [
                None,
                None,
                "2000",
                None,
                None,
            ],
        },
    }

    result = find_current_event(
        data=data,
        server=Server.TW,
        now_ms=3000,
    )

    assert result is None