"""Structured logging configuration using structlog.

Provides:
- JSON-formatted logs for log aggregation (ELK, Loki, etc.)
- ISO 8601 timestamps
- Context variable merging (correlation IDs, request IDs, etc.)
- Log level filtering
"""

import logging
import sys

import structlog


def setup_logging(log_level: str = "INFO"):
    """Configure structlog and standard logging.
    
    Sets up:
    - JSON output for structured logging
    - Context variable merging
    - ISO 8601 timestamps
    - Stack trace rendering
    - Filtering by log level
    
    Args:
        log_level: Log level string (INFO, DEBUG, WARNING, ERROR)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


log = structlog.get_logger()
