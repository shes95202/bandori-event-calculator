from dataclasses import dataclass

from bandori_event_calculator import bestdori
from bandori_event_calculator.app import (
    EventCalculation,
    calculate_event,
)
from bandori_event_calculator.bestdori import (
    EventSnapshot,
    Server,
)


@dataclass
class AppState:
    server: Server
    snapshot: EventSnapshot | None = None

    current_score: int = 0
    average_score: int = 0

    calculation: EventCalculation | None = None

    def refresh_bestdori(self) -> None:
        """Fetch fresh event data from Bestdori."""

        self.snapshot = bestdori.get_display_event_snapshot(
            self.server
        )

        self.recalculate()

    def update_current_score(
        self,
        current_score: int,
    ) -> None:
        """Update the user's current score and recalculate locally."""

        if current_score < 0:
            raise ValueError(
                "current_score cannot be negative"
            )

        self.current_score = current_score
        self.recalculate()

    def update_average_score(
        self,
        average_score: int,
    ) -> None:
        """Update the average score per game and recalculate locally."""

        if average_score < 0:
            raise ValueError(
                "average_score cannot be negative"
            )

        self.average_score = average_score
        self.recalculate()

    def recalculate(self) -> None:
        """
        Recalculate all results using the cached snapshot.

        This method never fetches data from Bestdori.
        """

        if self.snapshot is None:
            self.calculation = None
            return

        if self.average_score <= 0:
            self.calculation = None
            return

        self.calculation = calculate_event(
            snapshot=self.snapshot,
            current_score=self.current_score,
            average_score=self.average_score,
        )