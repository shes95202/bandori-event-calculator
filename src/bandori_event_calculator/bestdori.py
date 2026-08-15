from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any
from enum import IntEnum

import requests
import time

BASE_URL = "https://bestdori.com"
TAIWAN_TZ = timezone(timedelta(hours=8))

class Server(IntEnum):
    JP = 0
    EN = 1
    TW = 2
    CN = 3
    KR = 4
    

@dataclass(frozen=True)
class Cutoff:
    score: int
    timestamp_ms: int
    
    @property
    def datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp_ms / 1000, tz=timezone.utc)

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
        return self.start_datetime_utc.astimezone(TAIWAN_TZ)

    @property
    def end_datetime_local(self) -> datetime:
        return self.end_datetime_utc.astimezone(TAIWAN_TZ)

def fetch_tracker_data(server: Server, event_id: int,tier: int) -> dict[str, Any]:
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

def parse_cutoffs(data: dict[str, Any]) -> list[Cutoff]:
    """Convert raw Bestdori tracker data into Cutoff objects."""
    
    if not data.get("result"):
        raise ValueError("Bestdori returned an unsuccessful result")
    
    raw_cutoffs = data.get("cutoffs")
    
    if not isinstance(raw_cutoffs, list):
        raise ValueError("Bestdori response does not contain cutoff data")
    
    cutoff = [Cutoff(score=item["ep"], timestamp_ms=item["time"]) for item in raw_cutoffs]
    
    return sorted(cutoff, key=lambda cutoff: cutoff.timestamp_ms)

def fetch_cutoffs(server: Server, event_id: int, tier: int) -> list[Cutoff]:
    """Fetch and parse cutoff history from Bestdori."""
    
    data = fetch_tracker_data(server=server, event_id=event_id, tier=tier)
    
    return parse_cutoffs(data)

def get_latest_cutoff(server: Server, event_id: int, tier: int) -> Cutoff:
    """Get the most recent cutoff for an event tier."""
    
    cutoffs = fetch_cutoffs(server=server, event_id=event_id, tier=tier)
    
    if not cutoffs:
        raise ValueError("No cutoff data is available")

    return cutoffs[-1]

def fetch_events_data() -> dict[str, Any]:
    """Fetch all event data from Bestdori."""

    url = f"{BASE_URL}/api/events/all.5.json"

    response = requests.get(
        url,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()

def parse_events(data: dict[str, Any], server: Server) -> list[Event]:
    """Convert raw Bestdori event data into Event objects."""

    events = []

    for event_id, item in data.items():
        names = item.get("eventName")
        start_times = item.get("startAt")
        end_times = item.get("endAt")

        if not isinstance(names, list):
            continue

        if not isinstance(start_times, list):
            continue

        if not isinstance(end_times, list):
            continue

        server_index = int(server)

        name = names[server_index]
        start_at = start_times[server_index]
        end_at = end_times[server_index]

        # This event does not exist on this server.
        if name is None or start_at is None or end_at is None:
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

def find_current_event(data: dict[str, Any], server: Server,now_ms: int) -> Event:
    """Find the currently active event for a server."""

    events = parse_events(
        data=data,
        server=server,
    )

    active_events = [
        event
        for event in events
        if event.start_at_ms <= now_ms <= event.end_at_ms
    ]

    if not active_events:
        return None

    return max(
        active_events,
        key=lambda event: event.start_at_ms,
    )

def get_current_event(server: Server) -> Event | None:
    """Fetch and return the currently active event."""

    data = fetch_events_data()

    now_ms = int(time.time() * 1000)

    return find_current_event(
        data=data,
        server=server,
        now_ms=now_ms,
    )