from typing import Any

import requests

BASE_URL = "https://bestdori.com"

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