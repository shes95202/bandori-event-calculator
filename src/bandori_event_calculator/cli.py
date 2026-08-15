from bandori_event_calculator.app import calculate_event
from bandori_event_calculator.bestdori import (
    Server,
    get_current_event_snapshot,
)
from bandori_event_calculator.calculator import TargetCalculation


def choose_server() -> Server:
    """Ask the user to choose a game server."""

    print("選擇伺服器：")
    print("1. JP")
    print("2. TW")

    while True:
        choice = input("> ").strip()

        if choice == "1":
            return Server.JP

        if choice == "2":
            return Server.TW

        print("請輸入 1 或 2。")


def read_nonnegative_int(prompt: str) -> int:
    """Read a non-negative integer."""

    while True:
        value = input(prompt).strip().replace(",", "")

        try:
            number = int(value)
        except ValueError:
            print("請輸入有效的整數。")
            continue

        if number < 0:
            print("數字不能是負數。")
            continue

        return number


def read_positive_int(prompt: str) -> int:
    """Read a positive integer."""

    while True:
        number = read_nonnegative_int(prompt)

        if number == 0:
            print("數字必須大於 0。")
            continue

        return number


def format_score_gap(score_gap: int) -> str:
    """Format score gap as ahead / behind / on target."""

    if score_gap > 0:
        return f"落後 {score_gap:,}"

    if score_gap < 0:
        return f"超前 {abs(score_gap):,}"

    return "剛好達標"


def print_target_block(
    label: str,
    current_cutoff: int,
    predicted_score: int,
    expected_score: int,
    score_gap: int,
    calculation: TargetCalculation,
) -> None:
    """Print a ranking or pace target using the same format."""

    print()
    print(label)
    print("-" * 30)

    print(
        f"目前分數線："
        f"{current_cutoff:,}"
    )

    print(
        f"預測分數線："
        f"{predicted_score:,}"
    )

    print(
        f"目前應達分數："
        f"{expected_score:,}"
    )

    print(
        f"目前狀態："
        f"{format_score_gap(score_gap)}"
    )

    print()

    print(
        f"還差分數："
        f"{calculation.remaining_score:,}"
    )

    print(
        f"還需要："
        f"{calculation.required_games:,} 場"
    )

    print(
        f"需要火："
        f"{calculation.required_boosts:,}"
    )

    print(
        f"回火次數："
        f"{calculation.required_refills:,}"
    )

    print(
        f"需要星石："
        f"{calculation.required_stars:,}"
    )

    print(
        f"預估時間："
        f"{calculation.required_hours:.1f} 小時"
    )


def main() -> None:
    print()
    print("Bandori Event Calculator")
    print("=" * 40)
    print()

    server = choose_server()

    print()
    print("正在取得 Bestdori 資料...")

    snapshot = get_current_event_snapshot(server)

    if snapshot is None:
        print()
        print(
            f"{server.name} "
            "目前沒有進行中的活動。"
        )
        return

    event = snapshot.event

    print()
    print(
        f"目前活動："
        f"#{event.id} {event.name}"
    )

    print(
        f"類型："
        f"{event.event_type}"
    )

    print(
        "時間："
        f"{event.start_datetime_local:%Y-%m-%d %H:%M}"
        " ~ "
        f"{event.end_datetime_local:%Y-%m-%d %H:%M}"
    )

    print()

    current_score = read_nonnegative_int(
        "目前分數："
    )

    average_score = read_positive_int(
        "一場平均分數："
    )

    result = calculate_event(
        snapshot=snapshot,
        current_score=current_score,
        average_score=average_score,
    )

    # ---------------------------------------------------------
    # Event status
    # ---------------------------------------------------------

    print()
    print("=" * 50)
    print("活動狀態")
    print("=" * 50)

    print(
        f"活動進度："
        f"{result.progress:.1%}"
    )

    print(
        f"目前分數："
        f"{result.current_score:,}"
    )

    print(
        f"一場平均分數："
        f"{result.average_score:,}"
    )

    if result.projected_final_score is not None:
        print(
            "目前 Pace 預計最終分數："
            f"{result.projected_final_score:,}"
        )

    # ---------------------------------------------------------
    # Ranking targets
    #
    # Resource requirements here are calculated against
    # the FINAL predicted score.
    # ---------------------------------------------------------

    print()
    print("=" * 50)
    print("排名目標")
    print("=" * 50)

    for tier, tier_result in result.tiers.items():
        print_target_block(
            label=f"T{tier}",
            current_cutoff=tier_result.current_cutoff,
            predicted_score=tier_result.predicted_score,
            expected_score=tier_result.expected_score,
            score_gap=tier_result.score_gap,
            calculation=tier_result.calculation,
        )

    # ---------------------------------------------------------
    # Pace / interval targets
    #
    # Same display format, but resource requirements here
    # are calculated against the CURRENT expected score.
    # ---------------------------------------------------------

    if result.benchmarks:
        print()
        print("=" * 50)
        print("區間目標")
        print("=" * 50)

        for benchmark in result.benchmarks.values():
            print_target_block(
                label=benchmark.label,
                current_cutoff=benchmark.current_cutoff,
                predicted_score=benchmark.predicted_score,
                expected_score=benchmark.expected_score,
                score_gap=benchmark.score_gap,
                calculation=benchmark.calculation,
            )

    print()


if __name__ == "__main__":
    main()