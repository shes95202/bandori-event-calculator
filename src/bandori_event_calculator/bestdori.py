from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

BASE_URL = "https://bestdori.com"

@dataclass(frozen=True)
class Cutoff:
    score: int
    timestamp_ms: int
    
    @property
    def datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp_ms / 1000, tz=timezone.utc)

def fetch_tracker_data(
    server: int,
    event_id: int,
    tier: int,
) -> dict[str, Any]:
    """Fetch raw event tracker data from Bestdori."""

    url = f"{BASE_URL}/api/tracker/data"

    params = {
        "server": server,
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

def fetch_cutoffs(server: int, event_id: int, tier: int) -> list[Cutoff]:
    """Fetch and parse cutoff history from Bestdori."""
    
    data = fetch_tracker_data(server=server, event_id=event_id, tier=tier)
    
    return parse_cutoffs(data)

def get_latest_cutoff(server: int, event_id: int, tier: int) -> Cutoff:
    """Get the most recent cutoff for an event tier."""
    
    cutoffs = fetch_cutoffs(server=server, event_id=event_id, tier=tier)
    
    if not cutoffs:
        raise ValueError("No cutoff data is available")

    return cutoffs[-1]