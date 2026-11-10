"""Stream rolling trend samples as Server-Sent Events."""
import asyncio
import json
from math import isfinite
from time import monotonic


async def stream_trends(service, last_event_id):
    run_id, _, cursor = last_event_id.partition(":")
    try:
        since = float(cursor)
        if not run_id or not isfinite(since) or since < 0:
            raise ValueError
    except ValueError:
        run_id, since = None, None

    previous_status = None
    heartbeat_at = monotonic()
    while True:
        current_run, payload = await service.trend_frame(since, run_id)
        status = payload["status"]
        if current_run is None:
            run_id, since = None, None
            if status != previous_status:
                yield f"id:\nevent: status\ndata: {json.dumps({'status': status})}\n\n"
                heartbeat_at = monotonic()
        else:
            fresh_run = current_run != run_id
            newest = max(
                (point["time"] for series in payload["devices"].values()
                 for points in series.values() for point in points),
                default=None,
            )
            if fresh_run or newest is not None:
                run_id = current_run
                since = newest if newest is not None else 0
                event = "snapshot" if fresh_run else "points"
                yield f"id: {run_id}:{since}\nevent: {event}\ndata: {json.dumps(payload)}\n\n"
                heartbeat_at = monotonic()
        previous_status = status
        if monotonic() - heartbeat_at >= 10:
            yield ": keep-alive\n\n"
            heartbeat_at = monotonic()
        await asyncio.sleep(1)
