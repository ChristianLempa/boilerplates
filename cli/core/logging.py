"""
Logging utilities for the Boilerplates CLI.
"""

import logging
import sys


def setup_logging(log_level: str = "WARNING") -> logging.Logger:
    """Setup basic logging configuration."""
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stderr)]
    )

    return logging.getLogger("boilerplates")
