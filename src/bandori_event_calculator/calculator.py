import math

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