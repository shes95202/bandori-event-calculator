import os
import re
import time

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any

import requests
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


BASE_URL = "https://bestdori.com"


class Server(IntEnum):
    JP = 0
    EN = 1
    TW = 2
    CN = 3
    KR = 4


TRACKED_TIERS = {
    Server.JP: (500, 1000, 2000),
    Server.TW: (100, 500, 1000),
}


SERVER_SLUGS = {
    Server.JP: "jp",
    Server.TW: "tw",
}


@dataclass(frozen=True)
class Cutoff:
    score: int
    timestamp_ms: int

    @property
    def datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(
            self.timestamp_ms / 1000,
            tz=timezone.utc,
        )

    @property
    def datetime_local(self) -> datetime:
        return self.datetime_utc.astimezone()


@dataclass(frozen=True)
class Event:
    id: int
    server: Server
    name: str
    event_type: str
    start_at_ms: int
    end_at_ms: int

    @property
    def start_datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(
            self.start_at_ms / 1000,
            tz=timezone.utc,
        )

    @property
    def end_datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(
            self.end_at_ms / 1000,
            tz=timezone.utc,
        )

    @property
    def start_datetime_local(self) -> datetime:
        return self.start_datetime_utc.astimezone()

    @property
    def end_datetime_local(self) -> datetime:
        return self.end_datetime_utc.astimezone()


@dataclass(frozen=True)
class EventSnapshot:
    event: Event
    cutoffs: dict[int, Cutoff]
    predictions: dict[int, int]
    is_active: bool = True


@dataclass(frozen=True)
class RegressionResult:
    intercept: float
    slope: float
    r_squared: float


def get_playwright_profile_dir() -> Path:
    """
    Return the directory used for the persistent Playwright profile.

    On Windows:
        %LOCALAPPDATA%/BandoriEventCalculator/playwright-profile

    This prevents the browser profile from appearing next to the
    application executable.
    """

    local_app_data = os.getenv(
        "LOCALAPPDATA"
    )

    if local_app_data:
        app_data_dir = (
            Path(local_app_data)
            / "BandoriEventCalculator"
        )
    else:
        # Fallback for environments where LOCALAPPDATA
        # is not available.
        app_data_dir = (
            Path.home()
            / ".bandori-event-calculator"
        )

    profile_dir = (
        app_data_dir
        / "playwright-profile"
    )

    profile_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return profile_dir


def fetch_tracker_data(
    server: Server,
    event_id: int,
    tier: int,
) -> dict[str, Any]:
    """Fetch raw event tracker data from Bestdori."""

    url = f"{BASE_URL}/api/tracker/data"

    params = {
        "server": int(server),
        "event": event_id,
        "tier": tier,
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def parse_cutoffs(
    data: dict[str, Any],
) -> list[Cutoff]:
    """Convert raw Bestdori tracker data into Cutoff objects."""

    if not data.get("result"):
        raise ValueError(
            "Bestdori returned an unsuccessful result"
        )

    raw_cutoffs = data.get(
        "cutoffs"
    )

    if not isinstance(
        raw_cutoffs,
        list,
    ):
        raise ValueError(
            "Bestdori response does not contain cutoff data"
        )

    cutoffs = [
        Cutoff(
            score=item["ep"],
            timestamp_ms=item["time"],
        )
        for item in raw_cutoffs
    ]

    return sorted(
        cutoffs,
        key=lambda cutoff: cutoff.timestamp_ms,
    )


def fetch_cutoffs(
    server: Server,
    event_id: int,
    tier: int,
) -> list[Cutoff]:
    """Fetch and parse cutoff history from Bestdori."""

    data = fetch_tracker_data(
        server=server,
        event_id=event_id,
        tier=tier,
    )

    return parse_cutoffs(
        data
    )


def get_latest_cutoff(
    server: Server,
    event_id: int,
    tier: int,
) -> Cutoff:
    """Get the most recent cutoff for an event tier."""

    cutoffs = fetch_cutoffs(
        server=server,
        event_id=event_id,
        tier=tier,
    )

    if not cutoffs:
        raise ValueError(
            "No cutoff data is available"
        )

    return cutoffs[-1]


def fetch_events_data() -> dict[str, Any]:
    """Fetch all event data from Bestdori."""

    url = (
        f"{BASE_URL}/api/events/all.5.json"
    )

    response = requests.get(
        url,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def parse_events(
    data: dict[str, Any],
    server: Server,
) -> list[Event]:
    """Convert raw Bestdori event data into Event objects."""

    events: list[Event] = []

    for event_id, item in data.items():
        names = item.get(
            "eventName"
        )

        start_times = item.get(
            "startAt"
        )

        end_times = item.get(
            "endAt"
        )

        if not isinstance(
            names,
            list,
        ):
            continue

        if not isinstance(
            start_times,
            list,
        ):
            continue

        if not isinstance(
            end_times,
            list,
        ):
            continue

        server_index = int(
            server
        )

        name = names[
            server_index
        ]

        start_at = start_times[
            server_index
        ]

        end_at = end_times[
            server_index
        ]

        # This event does not exist on this server.
        if (
            name is None
            or start_at is None
            or end_at is None
        ):
            continue

        events.append(
            Event(
                id=int(event_id),
                server=server,
                name=name,
                event_type=item["eventType"],
                start_at_ms=int(start_at),
                end_at_ms=int(end_at),
            )
        )

    return sorted(
        events,
        key=lambda event: event.start_at_ms,
    )


def find_current_event(
    data: dict[str, Any],
    server: Server,
    now_ms: int,
) -> Event | None:
    """Find the currently active event for a server."""

    events = parse_events(
        data=data,
        server=server,
    )

    active_events = [
        event
        for event in events
        if (
            event.start_at_ms
            <= now_ms
            <= event.end_at_ms
        )
    ]

    if not active_events:
        return None

    return max(
        active_events,
        key=lambda event: event.start_at_ms,
    )


def find_previous_event(
    data: dict[str, Any],
    server: Server,
    now_ms: int,
) -> Event | None:
    """Find the most recently ended event for a server."""

    events = parse_events(
        data=data,
        server=server,
    )

    previous_events = [
        event
        for event in events
        if event.end_at_ms < now_ms
    ]

    if not previous_events:
        return None

    return max(
        previous_events,
        key=lambda event: event.end_at_ms,
    )


def get_current_event(
    server: Server,
) -> Event | None:
    """Fetch and return the currently active event."""

    data = fetch_events_data()

    now_ms = int(
        time.time() * 1000
    )

    return find_current_event(
        data=data,
        server=server,
        now_ms=now_ms,
    )


def get_tracked_tiers(
    server: Server,
) -> tuple[int, ...]:
    """Return the tiers tracked by the calculator for a server."""

    try:
        return TRACKED_TIERS[
            server
        ]
    except KeyError:
        raise ValueError(
            f"Server {server.name} is not supported"
        )


def get_event_tier_cutoffs(
    event: Event,
) -> dict[int, Cutoff]:
    """
    Get the latest available tracked tier cutoffs for a specific event.

    Bestdori can temporarily return an empty cutoff list just after an
    event starts.  That is a normal "data not ready yet" state and should
    not make the whole event snapshot fail.  Missing tiers are therefore
    skipped and will appear automatically on a later refresh once Bestdori
    has published cutoff data.
    """

    tiers = get_tracked_tiers(
        event.server
    )

    latest_cutoffs: dict[int, Cutoff] = {}

    for tier in tiers:
        cutoffs = fetch_cutoffs(
            server=event.server,
            event_id=event.id,
            tier=tier,
        )

        if not cutoffs:
            continue

        latest_cutoffs[tier] = cutoffs[-1]

    return latest_cutoffs


def get_current_tier_cutoffs(
    server: Server,
) -> dict[int, Cutoff] | None:
    """Get the latest tracked tier cutoffs for the current event."""

    event = get_current_event(
        server
    )

    if event is None:
        return None

    return get_event_tier_cutoffs(
        event
    )


def linear_regression(
    points: list[
        tuple[float, float]
    ],
) -> RegressionResult:
    """
    Perform simple linear regression.

    This function is retained from the earlier Bestdori
    prediction investigation and is also covered by tests.
    """

    if len(points) < 2:
        raise ValueError(
            "At least two points are required"
        )

    count = len(
        points
    )

    mean_x = (
        sum(
            x
            for x, _ in points
        )
        / count
    )

    mean_y = (
        sum(
            y
            for _, y in points
        )
        / count
    )

    covariance = sum(
        (x - mean_x)
        * (y - mean_y)
        for x, y in points
    )

    variance_x = sum(
        (x - mean_x) ** 2
        for x, _ in points
    )

    variance_y = sum(
        (y - mean_y) ** 2
        for _, y in points
    )

    if variance_x == 0:
        raise ValueError(
            "Cannot regress points with identical x values"
        )

    slope = (
        covariance
        / variance_x
    )

    intercept = (
        mean_y
        - slope * mean_x
    )

    if variance_y == 0:
        r_squared = 0.0

    else:
        std_x = (
            variance_x
            / count
        ) ** 0.5

        std_y = (
            variance_y
            / count
        ) ** 0.5

        correlation = (
            slope
            * std_x
            / std_y
        )

        r_squared = (
            correlation ** 2
        )

    return RegressionResult(
        intercept=intercept,
        slope=slope,
        r_squared=r_squared,
    )


def parse_latest_prediction_text(
    text: str,
) -> int:
    """Extract the latest prediction score from rendered Bestdori text."""

    labels = (
        "最新預測",
        "Latest Prediction",
    )

    for line in text.splitlines():
        line = line.strip()

        for label in labels:
            if line.startswith(
                label
            ):
                value_text = (
                    line[
                        len(label):
                    ]
                    .strip()
                )

                digits = re.sub(
                    r"\D",
                    "",
                    value_text,
                )

                if digits:
                    return int(
                        digits
                    )

    raise ValueError(
        "Latest prediction was not found"
    )


def get_event_tracker_url(
    server: Server,
    tier: int,
) -> str:
    """Return the Bestdori Event Tracker URL for a server/tier."""

    try:
        server_slug = SERVER_SLUGS[
            server
        ]
    except KeyError:
        raise ValueError(
            f"Server {server.name} is not supported"
        )

    return (
        f"{BASE_URL}/tool/eventtracker/"
        f"{server_slug}/t{tier}"
    )


def fetch_latest_predictions(
    server: Server,
) -> dict[int, int]:
    """
    Fetch all currently available Latest Prediction values from Bestdori.

    Immediately after an event starts, Bestdori may not have generated a
    prediction for every tracked tier yet.  A missing prediction is treated
    as temporarily unavailable rather than as a failure of the entire
    server refresh.
    """

    tiers = get_tracked_tiers(
        server
    )

    predictions: dict[
        int,
        int,
    ] = {}

    profile_dir = (
        get_playwright_profile_dir()
    )

    with sync_playwright() as p:
        context = (
            p.chromium.launch_persistent_context(
                user_data_dir=str(
                    profile_dir
                ),
                headless=True,
            )
        )

        try:
            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )

            for tier in tiers:
                url = get_event_tracker_url(
                    server=server,
                    tier=tier,
                )

                # Navigation/network errors are still real failures and are
                # allowed to propagate.  Only the expected "prediction not
                # available yet" condition is ignored.
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )

                try:
                    page.wait_for_function(
                        """
                        () =>
                            document.body.innerText.includes("最新預測") ||
                            document.body.innerText.includes("Latest Prediction")
                        """,
                        timeout=5_000,
                    )
                except PlaywrightTimeoutError:
                    continue

                text = (
                    page.locator(
                        "body"
                    )
                    .inner_text()
                )

                try:
                    predictions[tier] = (
                        parse_latest_prediction_text(
                            text
                        )
                    )
                except ValueError:
                    # The page loaded, but Bestdori has not published a
                    # usable prediction yet.  Try again on the next refresh.
                    continue

        finally:
            context.close()

    return predictions


def get_current_predictions(
    server: Server,
) -> dict[int, int] | None:
    """Fetch prediction values for the currently active event."""

    event = get_current_event(
        server
    )

    if event is None:
        return None

    return fetch_latest_predictions(
        server
    )


def get_current_event_snapshot(
    server: Server,
) -> EventSnapshot | None:
    """Fetch a complete snapshot of the current event."""

    event = get_current_event(
        server
    )

    if event is None:
        return None

    cutoffs = (
        get_current_tier_cutoffs(
            server
        )
    )

    predictions = (
        get_current_predictions(
            server
        )
    )

    if (
        cutoffs is None
        or predictions is None
    ):
        return None

    return EventSnapshot(
        event=event,
        cutoffs=cutoffs,
        predictions=predictions,
    )

def get_display_event_snapshot(
    server: Server,
) -> EventSnapshot | None:
    """
    Fetch the event snapshot that should be shown in the GUI.

    If an event is active, return the normal live snapshot with Bestdori
    predictions. During the gap between events, return the most recently
    ended event and reuse its final cutoffs as the final target scores so
    the GUI can keep the exact same calculation layout.
    """

    data = fetch_events_data()

    now_ms = int(
        time.time() * 1000
    )

    current_event = find_current_event(
        data=data,
        server=server,
        now_ms=now_ms,
    )

    if current_event is not None:
        cutoffs = get_event_tier_cutoffs(
            current_event
        )

        predictions = fetch_latest_predictions(
            server
        )

        return EventSnapshot(
            event=current_event,
            cutoffs=cutoffs,
            predictions=predictions,
            is_active=True,
        )

    previous_event = find_previous_event(
        data=data,
        server=server,
        now_ms=now_ms,
    )

    if previous_event is None:
        return None

    cutoffs = get_event_tier_cutoffs(
        previous_event
    )

    final_scores = {
        tier: cutoff.score
        for tier, cutoff in cutoffs.items()
    }

    return EventSnapshot(
        event=previous_event,
        cutoffs=cutoffs,
        predictions=final_scores,
        is_active=False,
    )

