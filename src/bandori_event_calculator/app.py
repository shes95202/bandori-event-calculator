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
    current_cutoff: int | None
    predicted_score: int | None
    expected_score: int | None
    score_gap: int | None
    calculation: TargetCalculation | None


@dataclass(frozen=True)
class BenchmarkResult:
    label: str
    current_cutoff: int | None
    predicted_score: int | None
    expected_score: int | None
    score_gap: int | None
    calculation: TargetCalculation | None


@dataclass(frozen=True)
class EventCalculation:
    snapshot: EventSnapshot
    current_score: int
    average_score: int
    progress: float
    projected_final_score: int | None
    tiers: dict[int, TierResult]
    benchmarks: dict[str, BenchmarkResult]


def _build_partial_target(
    *,
    tier: int,
    current_cutoff: int | None,
    predicted_score: int | None,
    current_score: int,
    average_score: int,
    progress: float,
) -> TierResult:
    """
    Build one ranking tier while preserving partially available Bestdori data.

    Cutoff and prediction data do not necessarily appear at the same time.
    Bestdori ranking data can appear progressively on every supported
    server. Higher-ranked tracked tiers may become available before lower
    tracked tiers. Keep whichever values already exist instead of hiding the
    whole tier until both cutoff and prediction are present.
    """

    if predicted_score is None:
        expected_score = None
        score_gap = None
        calculation = None
    else:
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

    return TierResult(
        tier=tier,
        current_cutoff=current_cutoff,
        predicted_score=predicted_score,
        expected_score=expected_score,
        score_gap=score_gap,
        calculation=calculation,
    )


def _build_benchmark(
    label: str,
    current_cutoff: int | None,
    predicted_score: int | None,
    current_score: int,
    average_score: int,
    progress: float,
) -> BenchmarkResult:
    """
    Build a pace benchmark while retaining any partial Bestdori data.

    A benchmark can expose its current cutoff before its prediction exists,
    or vice versa.  Prediction-dependent calculations are only produced once
    the prediction is available.
    """

    if predicted_score is None:
        expected_score = None
        score_gap = None
        calculation = None
    else:
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


def _maybe_average(
    first: int | None,
    second: int | None,
) -> int | None:
    if first is None or second is None:
        return None

    return calculate_tier_average(
        first,
        second,
    )


def _maybe_quartile(
    higher_score: int | None,
    lower_score: int | None,
    fraction: float,
) -> int | None:
    if higher_score is None or lower_score is None:
        return None

    return calculate_tier_quartile(
        higher_score=higher_score,
        lower_score=lower_score,
        fraction=fraction,
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
    # ---------------------------------------------------------

    tier_results: dict[int, TierResult] = {}

    # Cutoffs and predictions can arrive independently.  Build a result for
    # every tier for which Bestdori has published at least one of them.
    available_tiers = (
        set(snapshot.cutoffs)
        | set(snapshot.predictions)
    )

    for tier in sorted(available_tiers):
        cutoff = snapshot.cutoffs.get(tier)
        predicted_score = snapshot.predictions.get(tier)

        tier_results[tier] = _build_partial_target(
            tier=tier,
            current_cutoff=(
                cutoff.score
                if cutoff is not None
                else None
            ),
            predicted_score=predicted_score,
            current_score=current_score,
            average_score=average_score,
            progress=progress,
        )

    # ---------------------------------------------------------
    # Pace / interval benchmarks
    # ---------------------------------------------------------

    benchmarks: dict[str, BenchmarkResult] = {}

    if event.server == Server.JP:
        t500 = tier_results.get(500)
        t1000 = tier_results.get(1000)
        t2000 = tier_results.get(2000)

        if t2000 is not None:
            benchmarks["t2000"] = _build_benchmark(
                label="T2000",
                current_cutoff=t2000.current_cutoff,
                predicted_score=t2000.predicted_score,
                current_score=current_score,
                average_score=average_score,
                progress=progress,
            )

        average_current_cutoff = _maybe_average(
            (
                t500.current_cutoff
                if t500 is not None
                else None
            ),
            (
                t1000.current_cutoff
                if t1000 is not None
                else None
            ),
        )

        average_predicted_score = _maybe_average(
            (
                t500.predicted_score
                if t500 is not None
                else None
            ),
            (
                t1000.predicted_score
                if t1000 is not None
                else None
            ),
        )

        if (
            average_current_cutoff is not None
            or average_predicted_score is not None
        ):
            benchmarks["t500_t1000_average"] = _build_benchmark(
                label="T500-T1000 平均",
                current_cutoff=average_current_cutoff,
                predicted_score=average_predicted_score,
                current_score=current_score,
                average_score=average_score,
                progress=progress,
            )

    elif event.server == Server.TW:
        t100 = tier_results.get(100)
        t500 = tier_results.get(500)

        # Ranking data can appear progressively. These TW pace benchmarks
        # depend only on T100 and T500, so a missing T1000 must never block
        # data that is already available for their actual dependencies.
        average_current_cutoff = _maybe_average(
            (
                t100.current_cutoff
                if t100 is not None
                else None
            ),
            (
                t500.current_cutoff
                if t500 is not None
                else None
            ),
        )

        average_predicted_score = _maybe_average(
            (
                t100.predicted_score
                if t100 is not None
                else None
            ),
            (
                t500.predicted_score
                if t500 is not None
                else None
            ),
        )

        if (
            average_current_cutoff is not None
            or average_predicted_score is not None
        ):
            benchmarks["t100_t500_average"] = _build_benchmark(
                label="T100-T500 平均",
                current_cutoff=average_current_cutoff,
                predicted_score=average_predicted_score,
                current_score=current_score,
                average_score=average_score,
                progress=progress,
            )

        q1_current_cutoff = _maybe_quartile(
            higher_score=(
                t100.current_cutoff
                if t100 is not None
                else None
            ),
            lower_score=(
                t500.current_cutoff
                if t500 is not None
                else None
            ),
            fraction=0.25,
        )

        q1_predicted_score = _maybe_quartile(
            higher_score=(
                t100.predicted_score
                if t100 is not None
                else None
            ),
            lower_score=(
                t500.predicted_score
                if t500 is not None
                else None
            ),
            fraction=0.25,
        )

        if (
            q1_current_cutoff is not None
            or q1_predicted_score is not None
        ):
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
