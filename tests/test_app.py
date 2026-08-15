from bandori_event_calculator.app import calculate_event
from bandori_event_calculator.bestdori import (
    Cutoff,
    Event,
    EventSnapshot,
    Server,
)

import pytest


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

def test_calculate_event_pace():
    event = Event(
        id=339,
        server=Server.JP,
        name="Test Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
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

    result = calculate_event(
        snapshot=snapshot,
        current_score=1_000_000,
        average_score=20_000,
        now_ms=5_000,
    )

    assert result.progress == pytest.approx(0.5)
    assert result.projected_final_score == 2_000_000

    assert result.tiers[500].expected_score == 2_000_000
    assert result.tiers[500].score_gap == 1_000_000

    assert result.tiers[1000].expected_score == 1_500_000
    assert result.tiers[1000].score_gap == 500_000

    assert result.tiers[2000].expected_score == 1_000_000
    assert result.tiers[2000].score_gap == 0

    t2000_benchmark = result.benchmarks["t2000"]

    assert t2000_benchmark.label == "T2000"
    assert t2000_benchmark.current_cutoff == 1_000_000
    assert t2000_benchmark.predicted_score == 2_000_000
    assert t2000_benchmark.expected_score == 1_000_000
    assert t2000_benchmark.score_gap == 0

    assert t2000_benchmark.calculation.remaining_score == 0
    assert t2000_benchmark.calculation.required_games == 0


    average_benchmark = result.benchmarks["t500_t1000_average"]

    assert average_benchmark.label == "T500-T1000 平均"
    assert average_benchmark.current_cutoff == 1_750_000
    assert average_benchmark.predicted_score == 3_500_000
    assert average_benchmark.expected_score == 1_750_000
    assert average_benchmark.score_gap == 750_000

    assert average_benchmark.calculation.remaining_score == 750_000
    assert average_benchmark.calculation.required_games == 38
    
def test_calculate_event_tw_benchmarks():
    event = Event(
        id=321,
        server=Server.TW,
        name="Test TW Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            100: Cutoff(
                score=1_500_000,
                timestamp_ms=5_000,
            ),
            500: Cutoff(
                score=800_000,
                timestamp_ms=5_000,
            ),
            1000: Cutoff(
                score=500_000,
                timestamp_ms=5_000,
            ),
        },
        predictions={
            100: 2_000_000,
            500: 1_000_000,
            1000: 600_000,
        },
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=500_000,
        average_score=20_000,
        now_ms=5_000,
    )

    assert result.progress == pytest.approx(0.5)
    assert result.projected_final_score == 1_000_000

    average_benchmark = (
        result.benchmarks["t100_t500_average"]
    )

    assert average_benchmark.label == "T100-T500 平均"
    assert average_benchmark.current_cutoff == 1_150_000
    assert average_benchmark.predicted_score == 1_500_000
    assert average_benchmark.expected_score == 750_000
    assert average_benchmark.score_gap == 250_000

    assert average_benchmark.calculation.remaining_score == 250_000
    assert average_benchmark.calculation.required_games == 13


    q1_benchmark = result.benchmarks["t100_t500_q1"]

    assert q1_benchmark.label == "T100-T500 Q1"
    assert q1_benchmark.current_cutoff == 975_000
    assert q1_benchmark.predicted_score == 1_250_000
    assert q1_benchmark.expected_score == 625_000
    assert q1_benchmark.score_gap == 125_000

    assert q1_benchmark.calculation.remaining_score == 125_000
    assert q1_benchmark.calculation.required_games == 7