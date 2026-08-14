from bandori_event_calculator.calculator import calculate_required_games

def test_calculate_required_games():
    result = calculate_required_games(
        target_score=4042833,
        current_score=1137195,
        average_score=20235,
    )

    assert result == 144