"""Run the headless twin: python api_server.py (one process, no reloader)."""
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from hypercorn.asyncio import serve
from hypercorn.config import Config

from twin_api import create_app


async def main():
    # Existing model/config loaders use paths relative to the project root.
    root = Path(__file__).resolve().parent
    os.chdir(root)
    load_dotenv(root / ".env")
    logging.basicConfig(level=logging.INFO)
    config = Config()
    config.bind = [os.getenv("DIGITAL_TWIN_BIND", "127.0.0.1:8001")]
    config.use_reloader = False
    await serve(create_app(), config)


if __name__ == "__main__":
    asyncio.run(main())
