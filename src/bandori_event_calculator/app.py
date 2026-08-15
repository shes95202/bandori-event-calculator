from dataclasses import dataclass

from bandori_event_calculator.bestdori import EventSnapshot
from bandori_event_calculator.calculator import (
    TargetCalculation,
    calculate_target,
)


@dataclass(frozen=True)
class TierResult:
    tier: int
    current_cutoff: int
    predicted_score: int
    calculation: TargetCalculation


@dataclass(frozen=True)
class EventCalculation:
    snapshot: EventSnapshot
    current_score: int
    average_score: int
    tiers: dict[int, TierResult]


def calculate_event(
    snapshot: EventSnapshot,
    current_score: int,
    average_score: int,
) -> EventCalculation:
    """Calculate target requirements for every tracked tier."""

    tier_results = {}

    for tier, predicted_score in snapshot.predictions.items():
        cutoff = snapshot.cutoffs.get(tier)

        if cutoff is None:
            raise ValueError(
                f"Missing current cutoff for T{tier}"
            )

        calculation = calculate_target(
            target_score=predicted_score,
            current_score=current_score,
            average_score=average_score,
        )

        tier_results[tier] = TierResult(
            tier=tier,
            current_cutoff=cutoff.score,
            predicted_score=predicted_score,
            calculation=calculation,
        )

    return EventCalculation(
        snapshot=snapshot,
        current_score=current_score,
        average_score=average_score,
        tiers=tier_results,
    )