"""HTTP mapping only; simulation ownership lives in the service."""
from quart import Blueprint, Response, current_app, jsonify, request

from twin_api.trends_stream import stream_trends

simulation_bp = Blueprint("simulation", __name__)


def _live_response(**payload):
    response = jsonify(payload)
    response.headers["Cache-Control"] = "no-store"
    return response


@simulation_bp.get("/status")
async def get_status():
    return _live_response(status=await current_app.extensions["simulation"].status())


@simulation_bp.get("/trends/stream")
async def get_trends_stream():
    service = current_app.extensions["simulation"]
    response = Response(
        stream_trends(service, request.headers.get("Last-Event-ID", "")),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
    response.timeout = None
    return response


@simulation_bp.get("/event-history")
async def get_event_history():
    if set(request.args) - {"event_id"}:
        return jsonify(error="event_id is the only supported query parameter"), 400
    history = current_app.extensions["simulation"].event_history
    return _live_response(**history.read(request.args.get("event_id")))


@simulation_bp.get("/event-feasibility")
async def get_event_feasibility():
    event_id = request.args.get("event_id")
    if event_id is not None and not event_id.strip():
        return jsonify(error="event_id must not be empty"), 400
    report = current_app.extensions["simulation"].event_history.feasibility(event_id)
    if report is None:
        message = (
            "No running event has feasibility samples yet"
            if event_id is None else "No feasibility samples recorded for this event today"
        )
        return jsonify(error=message), 404
    return _live_response(**report)


@simulation_bp.get("/bees-dispatch-schedule")
async def get_dispatch():
    response = jsonify(await current_app.extensions["simulation"].dispatch())
    response.headers["Cache-Control"] = "no-store"
    return response


@simulation_bp.get("/snapshot")
async def get_snapshot():
    return _live_response(**await current_app.extensions["simulation"].snapshot())


@simulation_bp.post("/v2/snapshot")
async def snapshot_v2():
    body = await request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Expected a JSON object with devices and tags arrays"), 400

    devices = body.get("devices")
    tags = body.get("tags", [])
    for name, values in (("devices", devices), ("tags", tags)):
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not value.strip() for value in values
        ):
            return jsonify(error=f"{name} must be an array of non-empty strings"), 400

    service = current_app.extensions["simulation"]
    return _live_response(devices=await service.snapshot_v2(set(devices), set(tags) or None))


@simulation_bp.post("/start")
async def start_simulation():
    try:
        status, already_running = await current_app.extensions["simulation"].start()
    except Exception:
        current_app.logger.exception("Simulation startup failed")
        return jsonify(success=False, error="Simulation startup failed; check twin service logs"), 500
    messages = {
        "starting": "Simulation start request accepted; simulation is starting",
        "stopping": "Simulation is stopping; retry Start after it has stopped",
        "restarting": "Simulation is restarting",
        "running": "Simulation is already running",
    }
    return jsonify(
        success=True,
        status=status,
        already_running=already_running,
        message=messages[status],
    ), 200 if status == "running" else 202


@simulation_bp.post("/restart")
async def restart_simulation():
    try:
        status, _ = await current_app.extensions["simulation"].restart()
    except Exception:
        current_app.logger.exception("Simulation restart failed")
        return jsonify(success=False, error="Simulation restart failed; check twin service logs"), 500
    return jsonify(success=True, status=status, message="Simulation restarted")


@simulation_bp.post("/stop")
async def stop_simulation():
    try:
        status = await current_app.extensions["simulation"].stop()
    except Exception:
        current_app.logger.exception("Simulation stop failed")
        return jsonify(success=False, error="Simulation stop failed; check twin service logs"), 500
    return jsonify(
        success=True,
        status=status,
        already_stopped=status == "stopped",
        message="Simulation stop request accepted; simulation is stopping"
        if status == "stopping" else "Simulation is already stopped",
    ), 202 if status == "stopping" else 200
