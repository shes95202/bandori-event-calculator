import time
from dataclasses import dataclass

from bandori_event_calculator.bestdori import (
    EventSnapshot,
    Server,
)
from bandori_event_calculator.calculator import (
    TargetCalculation,
    calculate_event_progress,
    calculate_expected_score,
    calculate_projected_final_score,
    calculate_score_gap,
    calculate_target,
    calculate_tier_average,
    calculate_tier_quartile,
)


@dataclass(frozen=True)
class TierResult:
    tier: int
    current_cutoff: int
    predicted_score: int
    expected_score: int
    score_gap: int
    calculation: TargetCalculation


@dataclass(frozen=True)
class BenchmarkResult:
    label: str
    current_cutoff: int
    predicted_score: int
    expected_score: int
    score_gap: int
    calculation: TargetCalculation


@dataclass(frozen=True)
class EventCalculation:
    snapshot: EventSnapshot
    current_score: int
    average_score: int
    progress: float
    projected_final_score: int | None
    tiers: dict[int, TierResult]
    benchmarks: dict[str, BenchmarkResult]


def _build_benchmark(
    label: str,
    current_cutoff: int,
    predicted_score: int,
    current_score: int,
    average_score: int,
    progress: float,
) -> BenchmarkResult:
    """
    Build a pace benchmark.

    Unlike a normal ranking target, the resource calculation here answers:
    "How much do I need to play right now to catch up to the expected score
    at the current event progress?"
    """

    expected_score = calculate_expected_score(
        target_score=predicted_score,
        progress=progress,
    )

    score_gap = calculate_score_gap(
        expected_score=expected_score,
        current_score=current_score,
    )

    calculation = calculate_target(
        target_score=expected_score,
        current_score=current_score,
        average_score=average_score,
    )

    return BenchmarkResult(
        label=label,
        current_cutoff=current_cutoff,
        predicted_score=predicted_score,
        expected_score=expected_score,
        score_gap=score_gap,
        calculation=calculation,
    )


def calculate_event(
    snapshot: EventSnapshot,
    current_score: int,
    average_score: int,
    now_ms: int | None = None,
) -> EventCalculation:
    """Calculate event targets, pace, and resource requirements."""

    if now_ms is None:
        now_ms = int(time.time() * 1000)

    event = snapshot.event

    # ---------------------------------------------------------
    # Event progress
    # ---------------------------------------------------------

    progress = calculate_event_progress(
        start_at_ms=event.start_at_ms,
        end_at_ms=event.end_at_ms,
        now_ms=now_ms,
    )

    # Estimate final score if the user keeps the current pace.
    projected_final_score = (
        calculate_projected_final_score(
            current_score=current_score,
            progress=progress,
        )
        if progress > 0
        else None
    )

    # ---------------------------------------------------------
    # Ranking targets
    #
    # These calculations answer:
    # "How much do I still need to play to reach the FINAL
    #  predicted score?"
    # ---------------------------------------------------------

    tier_results: dict[int, TierResult] = {}

    for tier, predicted_score in snapshot.predictions.items():
        cutoff = snapshot.cutoffs.get(tier)

        # Bestdori may have a prediction before the first cutoff (or vice
        # versa) just after an event starts.  Only calculate a tier after
        # both pieces of data are available.
        if cutoff is None:
            continue

        expected_score = calculate_expected_score(
            target_score=predicted_score,
            progress=progress,
        )

        score_gap = calculate_score_gap(
            expected_score=expected_score,
            current_score=current_score,
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
            expected_score=expected_score,
            score_gap=score_gap,
            calculation=calculation,
        )

    # ---------------------------------------------------------
    # Pace / interval benchmarks
    #
    # These calculations answer:
    # "How much do I need to play RIGHT NOW to catch up
    #  to the expected score at the current progress?"
    # ---------------------------------------------------------

    benchmarks: dict[str, BenchmarkResult] = {}

    if event.server == Server.JP:
        # JP: T2000 benchmark can be shown as soon as T2000 is ready.
        if 2000 in tier_results:
            t2000 = tier_results[2000]

            benchmarks["t2000"] = _build_benchmark(
                label="T2000",
                current_cutoff=t2000.current_cutoff,
                predicted_score=t2000.predicted_score,
                current_score=current_score,
                average_score=average_score,
                progress=progress,
            )

        # JP: the average benchmark needs both T500 and T1000.
        if 500 in tier_results and 1000 in tier_results:
            average_current_cutoff = calculate_tier_average(
                tier_results[500].current_cutoff,
                tier_results[1000].current_cutoff,
            )

            average_predicted_score = calculate_tier_average(
                tier_results[500].predicted_score,
                tier_results[1000].predicted_score,
            )

            benchmarks["t500_t1000_average"] = _build_benchmark(
                label="T500-T1000 平均",
                current_cutoff=average_current_cutoff,
                predicted_score=average_predicted_score,
                current_score=current_score,
                average_score=average_score,
                progress=progress,
            )

    elif event.server == Server.TW:
        # Both TW pace benchmarks depend on T100 and T500.  If either tier
        # has not appeared on Bestdori yet, leave the benchmark pending
        # instead of failing the whole event.
        if 100 in tier_results and 500 in tier_results:
            average_current_cutoff = calculate_tier_average(
                tier_results[100].current_cutoff,
                tier_results[500].current_cutoff,
            )

            average_predicted_score = calculate_tier_average(
                tier_results[100].predicted_score,
                tier_results[500].predicted_score,
            )

            benchmarks["t100_t500_average"] = _build_benchmark(
                label="T100-T500 平均",
                current_cutoff=average_current_cutoff,
                predicted_score=average_predicted_score,
                current_score=current_score,
                average_score=average_score,
                progress=progress,
            )

            q1_current_cutoff = calculate_tier_quartile(
                higher_score=tier_results[100].current_cutoff,
                lower_score=tier_results[500].current_cutoff,
                fraction=0.25,
            )

            q1_predicted_score = calculate_tier_quartile(
                higher_score=tier_results[100].predicted_score,
                lower_score=tier_results[500].predicted_score,
                fraction=0.25,
            )

            benchmarks["t100_t500_q1"] = _build_benchmark(
                label="T100-T500 Q1",
                current_cutoff=q1_current_cutoff,
                predicted_score=q1_predicted_score,
                current_score=current_score,
                average_score=average_score,
                progress=progress,
            )

    return EventCalculation(
        snapshot=snapshot,
        current_score=current_score,
        average_score=average_score,
        progress=progress,
        projected_final_score=projected_final_score,
        tiers=tier_results,
        benchmarks=benchmarks,
    )