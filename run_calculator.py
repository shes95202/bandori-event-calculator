from bandori_event_calculator.app import calculate_event
from bandori_event_calculator.bestdori import (
    Server,
    get_current_event_snapshot,
)


snapshot = get_current_event_snapshot(Server.JP)

if snapshot is None:
    print("目前沒有進行中的日服活動。")
    raise SystemExit


print()
print(
    f"Event: #{snapshot.event.id} "
    f"{snapshot.event.name}"
)

print()

current_score = int(
    input("目前分數：").replace(",", "")
)

average_score = int(
    input("一場平均分數：").replace(",", "")
)

result = calculate_event(
    snapshot=snapshot,
    current_score=current_score,
    average_score=average_score,
)

print()
print("=" * 50)

for tier, tier_result in result.tiers.items():
    calculation = tier_result.calculation

    print()
    print(f"T{tier}")
    print(
        f"目前分數線："
        f"{tier_result.current_cutoff:,}"
    )
    print(
        f"預測分數線："
        f"{tier_result.predicted_score:,}"
    )
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