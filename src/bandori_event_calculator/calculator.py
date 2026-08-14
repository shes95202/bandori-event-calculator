import math
from dataclasses import dataclass

@dataclass
class TargetCalculation:
    remaining_score: int
    required_games: int
    required_boosts: int
    required_refills: int
    required_stars: int
    required_minutes: int
    required_hours: float

def calculate_target(
    target_score: int,
    current_score: int,
    average_score: int,
    boosts_per_game: int = 3,
    boosts_per_refill: int = 10,
    stars_per_refill: int = 100,
    minutes_per_game: int = 3,
) -> TargetCalculation:
    """Calculate resources required to reach a target event score."""
    
    if average_score <= 0:
        raise ValueError("average_score must be greater than 0")
    
    if boosts_per_game <= 0:
        raise ValueError("boosts_per_game must be greater than 0")
    
    remaining_score = max(target_score - current_score, 0)
    
    if remaining_score == 0:
        return TargetCalculation(
            remaining_score=0,
            required_games=0,
            required_boosts=0,
            required_refills=0,
            required_stars=0,
            required_minutes=0,
            required_hours=0.0,
        )
    required_games = math.ceil(remaining_score / average_score)
    
    required_boosts = required_games * boosts_per_game
    
    required_refills = math.ceil(required_boosts / boosts_per_refill)
    
    required_stars = required_refills * stars_per_refill
    
    required_minutes = required_games * minutes_per_game
    
    required_hours = required_minutes / 60
    
    return TargetCalculation(
        remaining_score=remaining_score,
        required_games=required_games,
        required_boosts=required_boosts,
        required_refills=required_refills,
        required_stars=required_stars,
        required_minutes=required_minutes,
        required_hours=required_hours,
    )

def calculate_required_games(
    target_score: int, 
    current_score: int, 
    average_score: int
)-> int:
    """Calculate how many games are required to reach the target score."""
    
    remainng_score = target_score - current_score
    
    if remainng_score <= 0:
        return 0
    
    if average_score <= 0:
        raise ValueError("average_score must be greater than 0")
    
    return math.ceil(remainng_score / average_score)

def calculate_projected_final_score(
    current_score: int,
    progress: float,
) -> int:
    """Estimate the final score based on the current event pace."""
    
    if not 0 < progress <= 1:
        raise ValueError("progress must be between 0 and 1")
    
    return round(current_score / progress)

def calculate_expected_score(
    target_score: int,
    progress: float,
) -> int:
    """Calculate the expected score at the current event progress."""

    if not 0 <= progress <= 1:
        raise ValueError("progress must be between 0 and 1")

    return round(target_score * progress)

def calculate_score_gap(
    expected_score: int,
    current_score: int,
) -> int:
    """Positive means behind target pace, negative means ahead."""

    return expected_score - current_score

def calculate_tier_quartile(
    higher_score: int,
    lower_score: int,
    fraction: float = 0.25,
) -> int:
    """
    Calculate a point between two tier scores.

    fraction=0.25 means 25% of the way from the lower score
    toward the higher score.
    """

    if not 0 <= fraction <= 1:
        raise ValueError("fraction must be between 0 and 1")

    return math.ceil(lower_score + (higher_score - lower_score) * fraction)
    
def calculate_tier_average(
    score_a: int,
    score_b: int,
) -> int:
    """Calculate the midpoint between two tier scores."""

    return math.ceil((score_a + score_b) / 2)