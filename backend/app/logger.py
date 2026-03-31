"""Centralized logging system with request ID tracking and file output."""

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime

# Context variable for request ID tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="NO_REQ")


class RequestIdFilter(logging.Filter):
    """Injects request_id into every log record."""
    def filter(self, record):
        record.request_id = request_id_var.get("NO_REQ")
        return True


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure and return the application logger."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    logger = logging.getLogger("financial_copilot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Prevent duplicate handlers on reload
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(request_id)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIdFilter())
    logger.addHandler(file_handler)

    return logger


def generate_request_id() -> str:
    """Generate a short unique request ID."""
    return uuid.uuid4().hex[:12]


# Initialize the global logger
logger = setup_logging()
