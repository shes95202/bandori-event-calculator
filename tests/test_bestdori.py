import pytest
import bandori_event_calculator.bestdori as bestdori

from bandori_event_calculator.bestdori import (
    Server,
    find_current_event,
    find_previous_event,
    parse_cutoffs,
    parse_events,
    get_tracked_tiers,
    parse_latest_prediction_text,
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



def test_find_previous_event():
    data = {
        "100": {
            "eventName": [
                "Older Event",
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
                "Latest Finished Event",
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

    result = find_previous_event(
        data=data,
        server=Server.JP,
        now_ms=6000,
    )

    assert result is not None
    assert result.id == 101
    assert result.name == "Latest Finished Event"

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

def test_get_tracked_tiers_for_jp():
    result = get_tracked_tiers(Server.JP)

    assert result == (500, 1000, 2000)


def test_get_tracked_tiers_for_tw():
    result = get_tracked_tiers(Server.TW)

    assert result == (100, 500, 1000)
    
def test_parse_latest_prediction_text_chinese():
    text = """
    最新分數線      202 1845
    最新預測        401 2183
    上次更新時間    7 分鐘前
    """

    result = parse_latest_prediction_text(text)

    assert result == 4_012_183

def test_parse_latest_prediction_text_english():
    text = """
    Current Cutoff    2,021,845
    Latest Prediction 4,012,183
    Last Updated      7 minutes ago
    """

    result = parse_latest_prediction_text(text)

    assert result == 4_012_183
    
def test_parse_latest_prediction_text_rejects_missing_prediction():
    with pytest.raises(ValueError):
        parse_latest_prediction_text(
            "Current Cutoff 2,021,845"
        )

def test_get_current_event_snapshot(monkeypatch):
    event = bestdori.Event(
        id=339,
        server=bestdori.Server.JP,
        name="parallel in the mirror",
        event_type="mission_live",
        start_at_ms=1000,
        end_at_ms=2000,
    )

    cutoffs = {
        500: bestdori.Cutoff(
            score=2_000_000,
            timestamp_ms=1500,
        ),
        1000: bestdori.Cutoff(
            score=1_500_000,
            timestamp_ms=1500,
        ),
        2000: bestdori.Cutoff(
            score=1_000_000,
            timestamp_ms=1500,
        ),
    }

    predictions = {
        500: 4_000_000,
        1000: 3_500_000,
        2000: 2_300_000,
    }

    monkeypatch.setattr(
        bestdori,
        "get_current_event",
        lambda server: event,
    )

    monkeypatch.setattr(
        bestdori,
        "get_current_tier_cutoffs",
        lambda server: cutoffs,
    )

    monkeypatch.setattr(
        bestdori,
        "get_current_predictions",
        lambda server: predictions,
    )

    result = bestdori.get_current_event_snapshot(
        bestdori.Server.JP
    )

    assert result is not None
    assert result.event == event
    assert result.cutoffs == cutoffs
    assert result.predictions == predictions

def test_get_current_event_snapshot_returns_none_when_inactive(monkeypatch):
    monkeypatch.setattr(
        bestdori,
        "get_current_event",
        lambda server: None,
    )

    result = bestdori.get_current_event_snapshot(
        bestdori.Server.TW
    )

    assert result is None

def test_get_display_event_snapshot_uses_previous_event(monkeypatch):
    previous_event = bestdori.Event(
        id=338,
        server=bestdori.Server.TW,
        name="Previous TW Event",
        event_type="mission_live",
        start_at_ms=1000,
        end_at_ms=2000,
    )

    cutoffs = {
        100: bestdori.Cutoff(
            score=3_000_000,
            timestamp_ms=2000,
        ),
        500: bestdori.Cutoff(
            score=2_000_000,
            timestamp_ms=2000,
        ),
        1000: bestdori.Cutoff(
            score=1_000_000,
            timestamp_ms=2000,
        ),
    }

    monkeypatch.setattr(
        bestdori,
        "fetch_events_data",
        lambda: {},
    )

    monkeypatch.setattr(
        bestdori,
        "find_current_event",
        lambda data, server, now_ms: None,
    )

    monkeypatch.setattr(
        bestdori,
        "find_previous_event",
        lambda data, server, now_ms: previous_event,
    )

    monkeypatch.setattr(
        bestdori,
        "get_event_tier_cutoffs",
        lambda event: cutoffs,
    )

    result = bestdori.get_display_event_snapshot(
        bestdori.Server.TW
    )

    assert result is not None
    assert result.event == previous_event
    assert result.cutoffs == cutoffs
    assert result.predictions == {
        100: 3_000_000,
        500: 2_000_000,
        1000: 1_000_000,
    }
    assert result.is_active is False


def test_get_display_event_snapshot_uses_current_event(monkeypatch):
    current_event = bestdori.Event(
        id=339,
        server=bestdori.Server.JP,
        name="Current JP Event",
        event_type="mission_live",
        start_at_ms=1000,
        end_at_ms=5000,
    )

    cutoffs = {
        500: bestdori.Cutoff(
            score=2_000_000,
            timestamp_ms=3000,
        ),
        1000: bestdori.Cutoff(
            score=1_500_000,
            timestamp_ms=3000,
        ),
        2000: bestdori.Cutoff(
            score=1_000_000,
            timestamp_ms=3000,
        ),
    }

    predictions = {
        500: 4_000_000,
        1000: 3_000_000,
        2000: 2_000_000,
    }

    monkeypatch.setattr(
        bestdori,
        "fetch_events_data",
        lambda: {},
    )

    monkeypatch.setattr(
        bestdori,
        "find_current_event",
        lambda data, server, now_ms: current_event,
    )

    monkeypatch.setattr(
        bestdori,
        "get_event_tier_cutoffs",
        lambda event: cutoffs,
    )

    monkeypatch.setattr(
        bestdori,
        "fetch_latest_predictions",
        lambda server: predictions,
    )

    result = bestdori.get_display_event_snapshot(
        bestdori.Server.JP
    )

    assert result is not None
    assert result.event == current_event
    assert result.cutoffs == cutoffs
    assert result.predictions == predictions
    assert result.is_active is True


def test_get_event_tier_cutoffs_skips_tiers_without_data(monkeypatch):
    event = bestdori.Event(
        id=324,
        server=bestdori.Server.TW,
        name="New TW Event",
        event_type="mission_live",
        start_at_ms=1_000,
        end_at_ms=10_000,
    )

    available = {
        100: [],
        500: [
            bestdori.Cutoff(
                score=123_456,
                timestamp_ms=2_000,
            )
        ],
        1000: [],
    }

    monkeypatch.setattr(
        bestdori,
        "fetch_cutoffs",
        lambda server, event_id, tier: available[tier],
    )

    result = bestdori.get_event_tier_cutoffs(event)

    assert list(result) == [500]
    assert result[500].score == 123_456
