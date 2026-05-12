from __future__ import annotations

import os

import structlog


def configure_logging() -> None:
    """Configure structlog: JSON in production (Railway), pretty in dev."""
    is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None

    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if is_production:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
