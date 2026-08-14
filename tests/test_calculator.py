import pytest
from bandori_event_calculator.calculator import (
    calculate_required_games,
    calculate_target,
    calculate_projected_final_score,
    calculate_expected_score,
    calculate_score_gap,
    calculate_tier_quartile,
    calculate_tier_average,
    calculate_challenge,
)

def test_calculate_required_games():
    result = calculate_required_games(
        target_score=4042833,
        current_score=1137195,
        average_score=20235,
    )

    assert result == 144

def test_calculate_required_games():
    result = calculate_required_games(
        target_score=4042833,
        current_score=1137195,
        average_score=20235,
    )

    assert result == 144


def test_calculate_target():
    result = calculate_target(
        target_score=4042833,
        current_score=1137195,
        average_score=20235,
    )

    assert result.remaining_score == 2905638
    assert result.required_games == 144
    assert result.required_boosts == 432
    assert result.required_refills == 44
    assert result.required_stars == 4400
    assert result.required_minutes == 432
    assert result.required_hours == 7.2


def test_target_already_reached():
    result = calculate_target(
        target_score=1_000_000,
        current_score=1_100_000,
        average_score=20_000,
    )

    assert result.required_games == 0
    assert result.required_boosts == 0
    assert result.required_stars == 0


def test_projected_final_score():
    result = calculate_projected_final_score(
        current_score=1_000_000,
        progress=0.5,
    )

    assert result == 2_000_000


def test_expected_score():
    result = calculate_expected_score(
        target_score=4_000_000,
        progress=0.25,
    )

    assert result == 1_000_000


def test_score_gap_when_behind():
    result = calculate_score_gap(
        expected_score=1_000_000,
        current_score=900_000,
    )

    assert result == 100_000


def test_tier_quartile():
    result = calculate_tier_quartile(
        higher_score=2_000_000,
        lower_score=1_000_000,
        fraction=0.25,
    )

    assert result == 1_250_000


def test_tier_average():
    result = calculate_tier_average(
        2_000_000,
        1_000_000,
    )

    assert result == 1_500_000
    
def test_calculate_challenge():
    result = calculate_challenge(
        coop_score=30_000,
        earned_cp=100,
        challenge_score=20_000,
        current_cp=500,
    )

    assert result.score_from_earned_cp == 10_000
    assert result.total_score_per_cycle == 40_000
    assert result.score_from_current_cp == 50_000

def test_challenge_with_no_current_cp():
    result = calculate_challenge(
        coop_score=30_000,
        earned_cp=100,
        challenge_score=20_000,
    )

    assert result.score_from_current_cp == 0

def test_challenge_rejects_invalid_cp_cost():
    with pytest.raises(ValueError):
        calculate_challenge(
            coop_score=30_000,
            earned_cp=100,
            challenge_score=20_000,
            cp_cost=0,
        )