"""In-memory state — deliberately dumb.

A real service keeps events in a database or durable queue. Here it's a
list that vanishes on restart — all a local demo needs.
"""

from datetime import datetime, timezone


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# every event broadcast so far
events: list[dict] = []
