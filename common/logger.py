"""
Simulator logging.
"""

from __future__ import annotations

import logging
from pathlib import Path


def create_logger(
    name: str,
    level: str = "INFO",
    directory: str = "logs",
) -> logging.Logger:

    Path(directory).mkdir(exist_ok=True)

    logger = logging.getLogger(name)

    logger.setLevel(level)

    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
    )

    console = logging.StreamHandler()

    console.setFormatter(formatter)

    logger.addHandler(console)

    file_handler = logging.FileHandler(
        Path(directory) / "simulation.log",
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.propagate = False

    return logger