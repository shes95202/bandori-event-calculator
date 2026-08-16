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

def test_calculate_event_tolerates_temporarily_missing_tier_data():
    event = Event(
        id=324,
        server=Server.TW,
        name="New TW Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            500: Cutoff(
                score=120_000,
                timestamp_ms=1_000,
            ),
        },
        predictions={
            100: 1_000_000,
            500: 600_000,
        },
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=100_000,
        average_score=10_000,
        now_ms=1_000,
    )

    # Cutoff and prediction availability are independent.  Keep T100's
    # prediction calculation even though its first cutoff has not appeared.
    t100 = result.tiers[100]
    assert t100.current_cutoff is None
    assert t100.predicted_score == 1_000_000
    assert t100.calculation is not None

    t500 = result.tiers[500]
    assert t500.current_cutoff == 120_000
    assert t500.predicted_score == 600_000
    assert result.progress == pytest.approx(0.1)

    # Since both predictions exist, the TW pace benchmark is usable even
    # though the averaged current cutoff is still waiting for T100 cutoff.
    average = result.benchmarks["t100_t500_average"]
    assert average.current_cutoff is None
    assert average.predicted_score == 800_000
    assert average.calculation is not None


def test_calculate_event_works_before_bestdori_has_any_tier_data():
    event = Event(
        id=324,
        server=Server.TW,
        name="New TW Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={},
        predictions={},
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=100_000,
        average_score=10_000,
        now_ms=1_000,
    )

    assert result.progress == pytest.approx(0.1)
    assert result.projected_final_score == 1_000_000
    assert result.tiers == {}
    assert result.benchmarks == {}


def test_tw_t100_cutoff_is_kept_before_prediction_and_lower_tiers():
    event = Event(
        id=324,
        server=Server.TW,
        name="New TW Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            100: Cutoff(
                score=250_000,
                timestamp_ms=1_000,
            ),
        },
        predictions={},
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=100_000,
        average_score=10_000,
        now_ms=1_000,
    )

    t100 = result.tiers[100]
    assert t100.current_cutoff == 250_000
    assert t100.predicted_score is None
    assert t100.expected_score is None
    assert t100.calculation is None

    assert 500 not in result.tiers
    assert 1000 not in result.tiers
    assert result.benchmarks == {}


def test_tw_t100_and_t500_cutoffs_build_partial_benchmarks_before_predictions():
    event = Event(
        id=324,
        server=Server.TW,
        name="New TW Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            100: Cutoff(
                score=300_000,
                timestamp_ms=1_000,
            ),
            500: Cutoff(
                score=100_000,
                timestamp_ms=1_000,
            ),
        },
        predictions={
            100: 1_000_000,
        },
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=100_000,
        average_score=10_000,
        now_ms=1_000,
    )

    assert result.tiers[100].predicted_score == 1_000_000
    assert result.tiers[100].calculation is not None

    assert result.tiers[500].current_cutoff == 100_000
    assert result.tiers[500].predicted_score is None
    assert result.tiers[500].calculation is None

    average = result.benchmarks["t100_t500_average"]
    assert average.current_cutoff == 200_000
    assert average.predicted_score is None
    assert average.calculation is None

    q1 = result.benchmarks["t100_t500_q1"]
    assert q1.current_cutoff == 150_000
    assert q1.predicted_score is None
    assert q1.calculation is None


def test_tw_t1000_missing_does_not_block_t100_t500_or_benchmarks():
    event = Event(
        id=324,
        server=Server.TW,
        name="New TW Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            100: Cutoff(
                score=300_000,
                timestamp_ms=1_000,
            ),
            500: Cutoff(
                score=100_000,
                timestamp_ms=1_000,
            ),
        },
        predictions={
            100: 1_000_000,
            500: 600_000,
        },
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=100_000,
        average_score=10_000,
        now_ms=1_000,
    )

    assert result.tiers[100].calculation is not None
    assert result.tiers[500].calculation is not None
    assert 1000 not in result.tiers

    average = result.benchmarks["t100_t500_average"]
    assert average.current_cutoff == 200_000
    assert average.predicted_score == 800_000
    assert average.calculation is not None

    q1 = result.benchmarks["t100_t500_q1"]
    assert q1.current_cutoff == 150_000
    assert q1.predicted_score == 700_000
    assert q1.calculation is not None



def test_jp_t500_cutoff_is_kept_before_prediction_and_lower_tiers():
    event = Event(
        id=340,
        server=Server.JP,
        name="New JP Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            500: Cutoff(
                score=350_000,
                timestamp_ms=1_000,
            ),
        },
        predictions={},
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=100_000,
        average_score=10_000,
        now_ms=1_000,
    )

    t500 = result.tiers[500]
    assert t500.current_cutoff == 350_000
    assert t500.predicted_score is None
    assert t500.expected_score is None
    assert t500.calculation is None

    assert 1000 not in result.tiers
    assert 2000 not in result.tiers
    assert result.benchmarks == {}


def test_jp_t500_and_t1000_partial_data_builds_only_available_benchmark_parts():
    event = Event(
        id=340,
        server=Server.JP,
        name="New JP Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            500: Cutoff(
                score=400_000,
                timestamp_ms=1_000,
            ),
            1000: Cutoff(
                score=200_000,
                timestamp_ms=1_000,
            ),
        },
        predictions={
            500: 1_200_000,
        },
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=100_000,
        average_score=10_000,
        now_ms=1_000,
    )

    assert result.tiers[500].predicted_score == 1_200_000
    assert result.tiers[500].calculation is not None

    assert result.tiers[1000].current_cutoff == 200_000
    assert result.tiers[1000].predicted_score is None
    assert result.tiers[1000].calculation is None

    average = result.benchmarks["t500_t1000_average"]
    assert average.current_cutoff == 300_000
    assert average.predicted_score is None
    assert average.calculation is None

    assert "t2000" not in result.benchmarks


def test_jp_t2000_missing_does_not_block_t500_t1000_or_average_benchmark():
    event = Event(
        id=340,
        server=Server.JP,
        name="New JP Event",
        event_type="mission_live",
        start_at_ms=0,
        end_at_ms=10_000,
    )

    snapshot = EventSnapshot(
        event=event,
        cutoffs={
            500: Cutoff(
                score=400_000,
                timestamp_ms=1_000,
            ),
            1000: Cutoff(
                score=200_000,
                timestamp_ms=1_000,
            ),
        },
        predictions={
            500: 1_200_000,
            1000: 800_000,
        },
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=100_000,
        average_score=10_000,
        now_ms=1_000,
    )

    assert result.tiers[500].calculation is not None
    assert result.tiers[1000].calculation is not None
    assert 2000 not in result.tiers

    average = result.benchmarks["t500_t1000_average"]
    assert average.current_cutoff == 300_000
    assert average.predicted_score == 1_000_000
    assert average.calculation is not None

    assert "t2000" not in result.benchmarks
