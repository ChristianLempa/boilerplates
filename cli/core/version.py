"""Version comparison utilities for semantic versioning.

This module provides utilities for parsing and comparing semantic version strings.
Supports version strings in the format: major.minor (e.g., "1.0", "1.2")
"""

from __future__ import annotations

import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def parse_version(version_str: str) -> Tuple[int, int]:
    """Parse a semantic version string into a tuple of integers.

    Args:
        version_str: Version string in format "major.minor" (e.g., "1.0", "1.2")

    Returns:
        Tuple of (major, minor) as integers

    Raises:
        ValueError: If version string is not in valid semantic version format

    Examples:
        >>> parse_version("1.0")
        (1, 0)
        >>> parse_version("1.2")
        (1, 2)
    """
    if not version_str:
        raise ValueError("Version string cannot be empty")

    # Remove 'v' prefix if present
    version_str = version_str.lstrip("v")

    # Match semantic version pattern: major.minor
    pattern = r"^(\d+)\.(\d+)$"
    match = re.match(pattern, version_str)

    if not match:
        raise ValueError(
            f"Invalid version format '{version_str}'. "
            "Expected format: major.minor (e.g., '1.0', '1.2')"
        )

    major, minor = match.groups()
    return (int(major), int(minor))


def compare_versions(version1: str, version2: str) -> int:
    """Compare two semantic version strings.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2

    Raises:
        ValueError: If either version string is invalid

    Examples:
        >>> compare_versions("1.0", "0.9")
        1
        >>> compare_versions("1.0", "1.0")
        0
        >>> compare_versions("1.0", "1.1")
        -1
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)

    if v1 < v2:
        return -1
    if v1 > v2:
        return 1
    return 0


def is_compatible(current_version: str, required_version: str) -> bool:
    """Check if current version meets the minimum required version.

    Args:
        current_version: Current version
        required_version: Minimum required version

    Returns:
        True if current_version >= required_version, False otherwise

    Examples:
        >>> is_compatible("1.0", "0.9")
        True
        >>> is_compatible("1.0", "1.0")
        True
        >>> is_compatible("1.0", "1.1")
        False
    """
    try:
        return compare_versions(current_version, required_version) >= 0
    except ValueError as e:
        logger.warning("Version compatibility check failed: %s", e)
        # If we can't parse versions, assume incompatible for safety
        return False
