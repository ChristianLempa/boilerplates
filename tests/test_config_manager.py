"""Tests for config migration behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml

from cli.core.config.config_manager import (
    DEFAULT_LIBRARY_BRANCH,
    DEFAULT_LIBRARY_DIRECTORY,
    DEFAULT_LIBRARY_NAME,
    DEFAULT_LIBRARY_URL,
    LEGACY_DEFAULT_LIBRARY_URL,
    ConfigManager,
    is_legacy_default_library_url,
)
from cli.core.exceptions import ConfigError


def _write_config(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_default_config_uses_new_library_repo(tmp_path: Path) -> None:
    """A fresh config should point at the new default template library."""
    config_path = tmp_path / "config.yaml"

    manager = ConfigManager(config_path=config_path)
    libraries = manager.get_libraries()

    assert len(libraries) == 1
    assert libraries[0]["name"] == DEFAULT_LIBRARY_NAME
    assert libraries[0]["url"] == DEFAULT_LIBRARY_URL
    assert libraries[0]["branch"] == DEFAULT_LIBRARY_BRANCH
    assert libraries[0]["directory"] == DEFAULT_LIBRARY_DIRECTORY


def test_migrate_legacy_default_library_and_queue_notice(tmp_path: Path) -> None:
    """Legacy christianlempa/boilerplates entries should be rewritten."""
    config_path = tmp_path / "config.yaml"
    ConfigManager.consume_migration_notices()
    _write_config(
        config_path,
        {
            "defaults": {},
            "preferences": {},
            "libraries": [
                {
                    "name": DEFAULT_LIBRARY_NAME,
                    "type": "git",
                    "url": LEGACY_DEFAULT_LIBRARY_URL,
                    "branch": "feature/test",
                    "directory": "library",
                    "enabled": True,
                },
                {
                    "name": "custom",
                    "type": "git",
                    "url": "https://github.com/example/custom-library.git",
                    "branch": "dev",
                    "directory": "templates",
                    "enabled": True,
                },
            ],
        },
    )

    manager = ConfigManager(config_path=config_path)
    libraries = manager.get_libraries()
    notices = ConfigManager.consume_migration_notices()

    assert libraries[0]["name"] == DEFAULT_LIBRARY_NAME
    assert libraries[0]["url"] == DEFAULT_LIBRARY_URL
    assert libraries[0]["branch"] == "feature/test"
    assert libraries[0]["directory"] == DEFAULT_LIBRARY_DIRECTORY
    assert libraries[0]["enabled"] is True

    assert libraries[1]["name"] == "custom"
    assert libraries[1]["url"] == "https://github.com/example/custom-library.git"
    assert libraries[1]["branch"] == "dev"
    assert libraries[1]["directory"] == "templates"

    assert len(notices) == 1
    assert "boilerplates-library" in notices[0].message
    assert "default" in notices[0].message

    # Notices are consumed once.
    assert ConfigManager.consume_migration_notices() == []


def test_does_not_migrate_custom_non_boilerplates_library(tmp_path: Path) -> None:
    """Non-matching custom library entries should be left untouched."""
    config_path = tmp_path / "config.yaml"
    ConfigManager.consume_migration_notices()
    _write_config(
        config_path,
        {
            "defaults": {},
            "preferences": {},
            "libraries": [
                {
                    "name": DEFAULT_LIBRARY_NAME,
                    "type": "git",
                    "url": "/Users/test/local/boilerplates",
                    "branch": "feature/test",
                    "directory": ".",
                    "enabled": True,
                }
            ],
        },
    )

    manager = ConfigManager(config_path=config_path)
    libraries = manager.get_libraries()

    assert libraries[0]["name"] == DEFAULT_LIBRARY_NAME
    assert libraries[0]["url"] == "/Users/test/local/boilerplates"
    assert libraries[0]["branch"] == "feature/test"
    assert libraries[0]["directory"] == "."
    assert ConfigManager.consume_migration_notices() == []


def test_migrates_any_library_pointing_to_legacy_boilerplates_repo(tmp_path: Path) -> None:
    """Any library URL pointing to christianlempa/boilerplates should migrate."""
    config_path = tmp_path / "config.yaml"
    ConfigManager.consume_migration_notices()
    _write_config(
        config_path,
        {
            "defaults": {},
            "preferences": {},
            "libraries": [
                {
                    "name": "custom",
                    "type": "git",
                    "url": "git@github.com:ChristianLempa/boilerplates.git",
                    "branch": "feature/test",
                    "directory": "templates",
                    "enabled": True,
                }
            ],
        },
    )

    manager = ConfigManager(config_path=config_path)
    libraries = manager.get_libraries()
    notices = ConfigManager.consume_migration_notices()

    assert libraries[0]["name"] == "custom"
    assert libraries[0]["url"] == DEFAULT_LIBRARY_URL
    assert libraries[0]["branch"] == "feature/test"
    assert libraries[0]["directory"] == DEFAULT_LIBRARY_DIRECTORY
    assert len(notices) == 1
    assert "custom" in notices[0].message


def test_legacy_library_url_matcher_handles_common_git_url_variants() -> None:
    """Legacy repo detection should match HTTPS and SSH GitHub URL forms."""
    assert is_legacy_default_library_url("https://github.com/christianlempa/boilerplates.git")
    assert is_legacy_default_library_url("https://github.com/ChristianLempa/boilerplates")
    assert is_legacy_default_library_url("git@github.com:ChristianLempa/boilerplates.git")
    assert not is_legacy_default_library_url("https://github.com/christianlempa/boilerplates-library.git")


def test_migration_write_failure_raises_config_error(tmp_path: Path) -> None:
    """Migration failures should surface as config errors instead of being swallowed."""
    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        {
            "defaults": {},
            "preferences": {},
            "libraries": [
                {
                    "name": DEFAULT_LIBRARY_NAME,
                    "type": "git",
                    "url": LEGACY_DEFAULT_LIBRARY_URL,
                    "branch": "main",
                    "directory": "library",
                    "enabled": True,
                }
            ],
        },
    )

    with patch.object(ConfigManager, "_write_config", side_effect=ConfigError("disk full")):
        try:
            ConfigManager(config_path=config_path)
        except ConfigError as exc:
            assert "disk full" in str(exc)
        else:
            raise AssertionError("Expected ConfigError for failed config migration write")
