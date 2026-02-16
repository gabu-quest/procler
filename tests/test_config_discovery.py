"""Tests for config directory discovery order.

Validates the documented discovery chain:
1. $PROCLER_CONFIG_DIR environment variable
2. .procler.env file (sets PROCLER_CONFIG_DIR)
3. .procler/ in current directory
4. .procler/ in git root
5. ~/.procler/ (global fallback)
"""

import os

import pytest

from procler.config import loader as config_loader
from procler.config.loader import find_config_dir, parse_env_file


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset config caches between tests."""
    config_loader.reset_config_cache()
    yield
    config_loader.reset_config_cache()


class TestEnvVarOverride:
    """$PROCLER_CONFIG_DIR takes highest priority."""

    def test_env_var_overrides_local_config(self, tmp_path):
        # Create both .procler/ and an env-specified dir
        local_config = tmp_path / ".procler"
        local_config.mkdir()
        env_config = tmp_path / "custom-config"
        env_config.mkdir()

        old_cwd = os.getcwd()
        old_env = os.environ.get("PROCLER_CONFIG_DIR")
        os.chdir(tmp_path)
        os.environ["PROCLER_CONFIG_DIR"] = str(env_config)
        config_loader.reset_config_cache()

        try:
            found = find_config_dir()
            assert found == env_config.resolve()
        finally:
            os.chdir(old_cwd)
            if old_env is None:
                os.environ.pop("PROCLER_CONFIG_DIR", None)
            else:
                os.environ["PROCLER_CONFIG_DIR"] = old_env
            config_loader.reset_config_cache()

    def test_env_var_resolves_tilde(self, tmp_path):
        old_env = os.environ.get("PROCLER_CONFIG_DIR")
        os.environ["PROCLER_CONFIG_DIR"] = "~/.test-procler-config"
        config_loader.reset_config_cache()

        try:
            found = find_config_dir()
            assert "~" not in str(found)
            assert ".test-procler-config" in str(found)
        finally:
            if old_env is None:
                os.environ.pop("PROCLER_CONFIG_DIR", None)
            else:
                os.environ["PROCLER_CONFIG_DIR"] = old_env
            config_loader.reset_config_cache()


class TestDotEnvFile:
    """.procler.env file sets PROCLER_CONFIG_DIR."""

    def test_env_file_sets_config_dir(self, tmp_path):
        custom_dir = tmp_path / "my-config"
        custom_dir.mkdir()
        env_file = tmp_path / ".procler.env"
        env_file.write_text(f'PROCLER_CONFIG_DIR={custom_dir}\n')

        old_cwd = os.getcwd()
        old_env = os.environ.pop("PROCLER_CONFIG_DIR", None)
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            found = find_config_dir()
            assert found == custom_dir.resolve()
        finally:
            os.chdir(old_cwd)
            if old_env is not None:
                os.environ["PROCLER_CONFIG_DIR"] = old_env
            config_loader.reset_config_cache()

    def test_env_file_relative_path(self, tmp_path):
        """Relative paths in .procler.env resolve relative to the env file."""
        custom_dir = tmp_path / "relative-config"
        custom_dir.mkdir()
        env_file = tmp_path / ".procler.env"
        env_file.write_text("PROCLER_CONFIG_DIR=relative-config\n")

        old_cwd = os.getcwd()
        old_env = os.environ.pop("PROCLER_CONFIG_DIR", None)
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            found = find_config_dir()
            assert found == custom_dir.resolve()
        finally:
            os.chdir(old_cwd)
            if old_env is not None:
                os.environ["PROCLER_CONFIG_DIR"] = old_env
            config_loader.reset_config_cache()


class TestLocalConfigDir:
    """.procler/ in current directory."""

    def test_finds_local_procler_dir(self, tmp_path):
        config_dir = tmp_path / ".procler"
        config_dir.mkdir()

        old_cwd = os.getcwd()
        old_env = os.environ.pop("PROCLER_CONFIG_DIR", None)
        os.chdir(tmp_path)
        config_loader.reset_config_cache()

        try:
            found = find_config_dir()
            assert found == config_dir
        finally:
            os.chdir(old_cwd)
            if old_env is not None:
                os.environ["PROCLER_CONFIG_DIR"] = old_env
            config_loader.reset_config_cache()


class TestGlobalFallback:
    """~/.procler/ is the last resort."""

    def test_falls_back_to_home(self, tmp_path):
        """When no local config exists, falls back to ~/.procler/."""
        old_cwd = os.getcwd()
        old_env = os.environ.pop("PROCLER_CONFIG_DIR", None)
        os.chdir(tmp_path)  # tmp_path has no .procler/
        config_loader.reset_config_cache()

        try:
            found = find_config_dir()
            # Should fall back to ~/.procler/ (home dir)
            expected = os.path.expanduser("~/.procler")
            assert str(found) == expected
        finally:
            os.chdir(old_cwd)
            if old_env is not None:
                os.environ["PROCLER_CONFIG_DIR"] = old_env
            config_loader.reset_config_cache()


class TestParseEnvFile:
    """parse_env_file utility."""

    def test_parse_key_value(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value\nOTHER=123\n")
        result = parse_env_file(env_file)
        assert result == {"KEY": "value", "OTHER": "123"}

    def test_parse_quoted_values(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('KEY="quoted value"\nKEY2=\'single quoted\'\n')
        result = parse_env_file(env_file)
        assert result["KEY"] == "quoted value"
        assert result["KEY2"] == "single quoted"

    def test_parse_skips_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nKEY=value\n")
        result = parse_env_file(env_file)
        assert result == {"KEY": "value"}

    def test_parse_skips_blank_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value\n\n\nOTHER=val\n")
        result = parse_env_file(env_file)
        assert len(result) == 2

    def test_parse_nonexistent_file(self, tmp_path):
        result = parse_env_file(tmp_path / "nonexistent")
        assert result == {}
