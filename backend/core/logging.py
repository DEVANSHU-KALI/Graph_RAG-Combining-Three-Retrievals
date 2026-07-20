# backend/core/logging.py

import logging


# Create logger object
logger = logging.getLogger("HybridGraphRAG")


# Set logging level
logger.setLevel(logging.INFO)


# Prevent duplicate logs
logger.propagate = False


# Create console handler
console_handler = logging.StreamHandler()


# Create log format
log_format = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


# Attach formatter to handler
console_handler.setFormatter(log_format)


# Avoid duplicate handlers
if not logger.handlers:
    logger.addHandler(console_handler)