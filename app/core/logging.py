"""
app.core.logging
~~~~~~~~~~~~~~~~
Thin compatibility shim — delegates entirely to associazione_toolkit.logging.

All modules in the app should import from here (not directly from the toolkit),
so if the toolkit API ever changes, there is a single place to update.

Usage::

    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("socio created", socio_id=42)
"""

from associazione_toolkit.logging import (
    bind_request_id,
    configure_logging,
    get_logger,
)

__all__ = [
    "configure_logging",
    "get_logger",
    "bind_request_id",
]


def setup_logging(level: str = "INFO", render_json: bool = True) -> None:
    """
    Backward-compatible alias for configure_logging().
    Called from main.py at startup.
    """
    configure_logging(level=level, render_json=render_json)
