"""HTTP mapping only; simulation ownership lives in the service."""
import asyncio
import json

from math import isfinite

from quart import Blueprint, Response, current_app, jsonify, request

from models.protection import ProtectionManager
from twin_api.custom_config import InvalidConfiguration
from twin_api.trends_stream import stream_trends

simulation_bp = Blueprint("simulation", __name__)
BANK_FAULTS = {
    "voltage": (480, "V", ProtectionManager.BASE_VOLTAGE * ProtectionManager.MIN_VOLTAGE_PU,
                ProtectionManager.BASE_VOLTAGE * ProtectionManager.MAX_VOLTAGE_PU),
    "frequency": (53, "Hz", ProtectionManager.MIN_FREQUENCY_HZ, ProtectionManager.MAX_FREQUENCY_HZ),
    "temperature": (56, "°C", None, ProtectionManager.MAX_TEMPERATURE_C),
}


def _live_response(**payload):
    response = jsonify(payload)
    response.headers["Cache-Control"] = "no-store"
    return response


@simulation_bp.get("/configuration/read")
async def read_configuration():
    service = current_app.extensions["simulation"]
    return _live_response(**await service.configuration())


@simulation_bp.post("/configuration")
async def post_configuration():
    service = current_app.extensions["simulation"]
    try:
        configuration = await service.update_configuration(await request.get_json(silent=True))
    except InvalidConfiguration as error:
        return jsonify(error=str(error)), 400
    if configuration is None:
        return jsonify(error="Wait for the simulation transition to finish"), 409
    return _live_response(configuration=configuration, applies_on_rebuild=True)


@simulation_bp.post("/grid-availability")
async def post_grid_availability():
    body = await request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"available"} or not isinstance(body["available"], bool):
        return jsonify(error="Send available as a JSON boolean"), 400
    service = current_app.extensions["simulation"]
    result = await service.update_grid_availability(body["available"])
    if result is None:
        return jsonify(error="Wait for the simulation transition to finish"), 409
    return _live_response(**result)


@simulation_bp.post("/bank-fault")
async def post_bank_fault():
    body = await request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) - {"device_id", "type", "enabled", "value"}:
        return jsonify(error="Send device_id, type, and enabled; value is optional"), 400
    device_id, kind, enabled = body.get("device_id"), body.get("type"), body.get("enabled")
    if not isinstance(device_id, str) or not device_id.strip() or not isinstance(enabled, bool):
        return jsonify(error="device_id must be a PCS ID and enabled must be a boolean"), 400
    if not isinstance(kind, str) or kind not in BANK_FAULTS:
        return jsonify(error="type must be voltage, frequency, or temperature"), 400
    default, unit, lower, upper = BANK_FAULTS[kind]
    value = None
    if enabled:
        value = body.get("value", default)
        if (
            type(value) not in (int, float) or not isfinite(value)
            or (lower is not None and value < 0)
            or not (value > upper or (lower is not None and value < lower))
        ):
            return jsonify(error=f"value must trigger the selected protection check ({unit})"), 400
    elif "value" in body:
        return jsonify(error="Omit value when clearing a bank fault"), 400

    service = current_app.extensions["simulation"]
    try:
        applied = await service.update_bank_fault(device_id, kind, value)
    except KeyError:
        return jsonify(error=f"Unknown PCS: {device_id}"), 404
    if not applied:
        return jsonify(error="Start the simulation before changing a live bank fault"), 409
    return _live_response(device_id=device_id, type=kind, enabled=enabled, value=value, unit=unit)


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


@simulation_bp.get("/load-shedding/stream")
async def get_load_shedding_stream():
    service = current_app.extensions["simulation"]
    event_id = request.args.get("event_id")
    return _changed_payload_stream("load_shedding", lambda: service.load_shedding(event_id))


@simulation_bp.get("/campus-load-trend/stream")
async def get_campus_load_trend_stream():
    service = current_app.extensions["simulation"]
    return _changed_payload_stream("campus_load_trend", service.campus_load_trend)


def _changed_payload_stream(event, read_payload):
    async def updates():
        previous = None
        while True:
            payload = await read_payload()
            if payload != previous:
                yield f"event: {event}\ndata: {json.dumps(payload)}\n\n"
                previous = payload
            else:
                yield ": keep-alive\n\n"
            await asyncio.sleep(1)

    response = Response(
        updates(), mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
    response.timeout = None
    return response


@simulation_bp.get("/bees-dispatch-schedule/stream")
async def get_dispatch_stream():
    service = current_app.extensions["simulation"]

    async def updates():
        previous_rows = None
        while True:
            payload = await service.dispatch()
            rows = payload["rows"]
            if rows == previous_rows:
                payload = {key: value for key, value in payload.items() if key != "rows"}
            else:
                previous_rows = rows
            yield f"event: dispatch\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(1)

    response = Response(
        updates(), mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
    response.timeout = None
    return response


@simulation_bp.get("/dispatch-notifications/stream")
async def get_dispatch_notifications_stream():
    """Send one popup notification per active dispatch interval."""
    service = current_app.extensions["simulation"]
    last_notification = request.headers.get("Last-Event-ID")

    async def updates():
        previous = last_notification
        while True:
            snapshot = await service.dispatch()
            interval = snapshot["current_interval"]
            frame = ": keep-alive\n\n"
            if interval and (event_id := interval.get("event_id")):
                time_stamp = interval["time_stamp"]
                notification_id = json.dumps([event_id, time_stamp])
                if notification_id != previous:
                    payload = {
                        "event_id": event_id,
                        "time_stamp": time_stamp,
                        "decision": interval.get("decision"),
                        "load_kw": interval.get("load_kw"),
                        "soc_percent": interval.get("soc_percent"),
                        "window_minutes": 15,
                    }
                    previous = notification_id
                    frame = (
                        f"id: {notification_id}\nevent: dispatch_notification\n"
                        f"data: {json.dumps(payload)}\n\n"
                    )
            yield frame
            await asyncio.sleep(1)

    response = Response(
        updates(), mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
    response.timeout = None
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
