from bandori_event_calculator.app import calculate_event
from bandori_event_calculator.bestdori import (
    Cutoff,
    Event,
    EventSnapshot,
    Server,
)


def test_calculate_event():
    event = Event(
        id=339,
        server=Server.JP,
        name="parallel in the mirror",
        event_type="mission_live",
        start_at_ms=1000,
        end_at_ms=2000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            500: Cutoff(
                score=2_000_000,
                timestamp_ms=1500,
            ),
            1000: Cutoff(
                score=1_500_000,
                timestamp_ms=1500,
            ),
            2000: Cutoff(
                score=1_000_000,
                timestamp_ms=1500,
            ),
        },
        predictions={
            500: 4_000_000,
            1000: 3_000_000,
            2000: 2_000_000,
        },
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=1_000_000,
        average_score=20_000,
    )

    assert result.current_score == 1_000_000
    assert result.average_score == 20_000

    assert result.tiers[500].current_cutoff == 2_000_000
    assert result.tiers[500].predicted_score == 4_000_000

    assert (
        result.tiers[500]
        .calculation
        .required_games
        == 150
    )

    assert (
        result.tiers[1000]
        .calculation
        .required_games
        == 100
    )

    assert (
        result.tiers[2000]
        .calculation
        .required_games
        == 50
    )