from bandori_event_calculator.bestdori import (
    Cutoff,
    Event,
    EventSnapshot,
    Server,
)
from bandori_event_calculator.state import AppState


def make_jp_snapshot() -> EventSnapshot:
    event = Event(
        id=339,
        server=Server.JP,
        name="Test Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    return EventSnapshot(
        event=event,
        cutoffs={
            500: Cutoff(
                score=2_000_000,
                timestamp_ms=5_000,
            ),
            1000: Cutoff(
                score=1_500_000,
                timestamp_ms=5_000,
            ),
            2000: Cutoff(
                score=1_000_000,
                timestamp_ms=5_000,
            ),
        },
        predictions={
            500: 4_000_000,
            1000: 3_000_000,
            2000: 2_000_000,
        },
    )

def test_update_current_score_recalculates():
    state = AppState(
        server=Server.JP,
        snapshot=make_jp_snapshot(),
        average_score=20_000,
    )

    state.update_current_score(
        1_000_000
    )

    assert state.calculation is not None
    assert state.calculation.current_score == 1_000_000

    first_games = (
        state.calculation
        .tiers[500]
        .calculation
        .required_games
    )

    state.update_current_score(
        2_000_000
    )

    assert state.calculation is not None
    assert state.calculation.current_score == 2_000_000

    second_games = (
        state.calculation
        .tiers[500]
        .calculation
        .required_games
    )

    assert second_games < first_games

def test_update_average_score_recalculates():
    state = AppState(
        server=Server.JP,
        snapshot=make_jp_snapshot(),
        current_score=1_000_000,
    )

    state.update_average_score(
        20_000
    )

    assert state.calculation is not None

    first_games = (
        state.calculation
        .tiers[500]
        .calculation
        .required_games
    )

    state.update_average_score(
        40_000
    )

    assert state.calculation is not None

    second_games = (
        state.calculation
        .tiers[500]
        .calculation
        .required_games
    )

    assert second_games < first_games

def test_update_current_score_does_not_fetch_bestdori(
    monkeypatch,
):
    def fail_if_called(server):
        raise AssertionError(
            "Bestdori should not be fetched"
        )

    monkeypatch.setattr(
        "bandori_event_calculator.state."
        "bestdori.get_current_event_snapshot",
        fail_if_called,
    )

    state = AppState(
        server=Server.JP,
        snapshot=make_jp_snapshot(),
        average_score=20_000,
    )

    state.update_current_score(
        1_500_000
    )

    assert state.calculation is not None

def test_refresh_bestdori(
    monkeypatch,
):
    snapshot = make_jp_snapshot()

    monkeypatch.setattr(
        "bandori_event_calculator.state."
        "bestdori.get_current_event_snapshot",
        lambda server: snapshot,
    )

    state = AppState(
        server=Server.JP,
        current_score=1_000_000,
        average_score=20_000,
    )

    assert state.snapshot is None

    state.refresh_bestdori()

    assert state.snapshot == snapshot
    assert state.calculation is not None