"""Structured logging configuration using structlog.

Configures structlog with JSON rendering for production and
human-readable pretty printing for local development.
"""
import logging
import sys
from typing import Any

try:
    import structlog

    def configure_logging(log_level: str = "INFO", env: str = "production") -> None:
        """Configures structlog for the application.

        Args:
            log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
            env: Environment name. Non-production uses pretty console renderer.
        """
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        if env == "development":
            processors.append(structlog.dev.ConsoleRenderer())
        else:
            processors.append(structlog.processors.JSONRenderer())

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level.upper(), logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(sys.stdout),
            cache_logger_on_first_use=True,
        )

    def get_logger(name: str = "fail") -> Any:
        """Returns a structured logger instance.

        Args:
            name: Logger name for context identification.

        Returns:
            structlog bound logger.
        """
        return structlog.get_logger(name)

except ImportError:
    # Fallback to stdlib logging when structlog is unavailable
    def configure_logging(log_level: str = "INFO", env: str = "production") -> None:  # type: ignore
        """Configure stdlib logging as fallback."""
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
            stream=sys.stdout,
        )

    def get_logger(name: str = "fail") -> logging.Logger:  # type: ignore
        """Returns stdlib logger as fallback."""
        return logging.getLogger(name)
