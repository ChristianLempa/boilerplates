"""Unit tests for version comparison utilities."""

import pytest

from cli.core.version import compare_versions, is_compatible, parse_version


class TestParseVersion:
    """Tests for parse_version function."""

    def test_parse_simple_version(self):
        """Test parsing simple version string."""
        assert parse_version("1.0") == (1, 0)
        assert parse_version("1.2") == (1, 2)
        assert parse_version("2.5") == (2, 5)

    def test_parse_version_with_v_prefix(self):
        """Test parsing version with 'v' prefix."""
        assert parse_version("v1.0") == (1, 0)
        assert parse_version("v2.3") == (2, 3)

    def test_parse_version_empty_string(self):
        """Test parsing empty string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_version("")

    def test_parse_version_invalid_format(self):
        """Test parsing invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid version format"):
            parse_version("1")
        with pytest.raises(ValueError, match="Invalid version format"):
            parse_version("1.2.3")
        with pytest.raises(ValueError, match="Invalid version format"):
            parse_version("invalid")


class TestCompareVersions:
    """Tests for compare_versions function."""

    def test_compare_equal_versions(self):
        """Test comparing equal versions."""
        assert compare_versions("1.0", "1.0") == 0
        assert compare_versions("2.5", "2.5") == 0

    def test_compare_major_version_difference(self):
        """Test comparing versions with different major numbers."""
        assert compare_versions("2.0", "1.0") == 1
        assert compare_versions("1.0", "2.0") == -1

    def test_compare_minor_version_difference(self):
        """Test comparing versions with different minor numbers."""
        assert compare_versions("1.2", "1.0") == 1
        assert compare_versions("1.0", "1.2") == -1

    def test_compare_with_v_prefix(self):
        """Test comparing versions with 'v' prefix."""
        assert compare_versions("v1.0", "v1.0") == 0
        assert compare_versions("v1.2", "v1.0") == 1

    @pytest.mark.parametrize(
        "v1,v2,expected",
        [
            ("1.0", "1.0", 0),
            ("1.1", "1.0", 1),
            ("1.0", "1.1", -1),
            ("2.0", "1.9", 1),
            ("0.9", "1.0", -1),
        ],
    )
    def test_compare_versions_parametrized(self, v1, v2, expected):
        """Test comparing various version combinations."""
        assert compare_versions(v1, v2) == expected


class TestIsCompatible:
    """Tests for is_compatible function."""

    def test_compatible_equal_versions(self):
        """Test compatibility with equal versions."""
        assert is_compatible("1.0", "1.0") is True

    def test_compatible_newer_version(self):
        """Test compatibility with newer current version."""
        assert is_compatible("1.2", "1.0") is True
        assert is_compatible("2.0", "1.0") is True

    def test_incompatible_older_version(self):
        """Test incompatibility with older current version."""
        assert is_compatible("1.0", "1.2") is False
        assert is_compatible("1.0", "2.0") is False

    def test_incompatible_invalid_versions(self):
        """Test that invalid versions return False for safety."""
        assert is_compatible("invalid", "1.0") is False
        assert is_compatible("1.0", "invalid") is False

    @pytest.mark.parametrize(
        "current,required,expected",
        [
            ("1.0", "1.0", True),
            ("1.2", "1.0", True),
            ("2.0", "1.0", True),
            ("1.0", "1.2", False),
            ("0.9", "1.0", False),
        ],
    )
    def test_is_compatible_parametrized(self, current, required, expected):
        """Test compatibility checks with various version combinations."""
        assert is_compatible(current, required) is expected
