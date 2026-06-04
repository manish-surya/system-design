"""ZEA logging setup using Rich."""
from __future__ import annotations

import logging
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
