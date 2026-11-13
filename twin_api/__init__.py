"""Headless digital twin HTTP application."""
from quart import Quart, request

from twin_api.routes import simulation_bp
from twin_api.service import SimulationService


ALLOWED_ORIGINS = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
]


def create_app(service=None):
    app = Quart(__name__)
    app.extensions["simulation"] = service if service is not None else SimulationService()
    app.register_blueprint(simulation_bp, url_prefix="/api/simulation")

    @app.after_request
    async def allow_frontend_origin(response):
        response.vary.add("Origin")
        origin = request.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            if request.method == "OPTIONS":
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Last-Event-ID"
        return response

    @app.after_serving
    async def shutdown_simulation():
        await app.extensions["simulation"].close()

    return app
