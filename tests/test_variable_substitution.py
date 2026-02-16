"""Tests for variable substitution system.

Tests the ${VAR} replacement logic, missing variable handling,
suspicious pattern detection, and config-based substitution.
"""

import logging

import pytest

from procler.core.variable_substitution import substitute_vars, warn_suspicious_vars


class TestSubstituteVars:
    """Core variable substitution logic."""

    def test_simple_replacement(self):
        result = substitute_vars("hello ${NAME}", {"NAME": "world"})
        assert result == "hello world"

    def test_multiple_replacements(self):
        result = substitute_vars("${HOST}:${PORT}", {"HOST": "localhost", "PORT": "8080"})
        assert result == "localhost:8080"

    def test_missing_var_kept_as_is(self):
        result = substitute_vars("echo ${UNKNOWN}", {"OTHER": "val"})
        assert result == "echo ${UNKNOWN}"

    def test_empty_vars_dict(self):
        result = substitute_vars("echo ${VAR}", {})
        assert result == "echo ${VAR}"

    def test_no_vars_in_text(self):
        result = substitute_vars("echo hello", {"VAR": "value"})
        assert result == "echo hello"

    def test_adjacent_vars(self):
        result = substitute_vars("${A}${B}", {"A": "foo", "B": "bar"})
        assert result == "foobar"

    def test_var_in_path(self):
        result = substitute_vars("/opt/${APP}/bin/${CMD}", {"APP": "myapp", "CMD": "run"})
        assert result == "/opt/myapp/bin/run"

    def test_partial_match_no_replace(self):
        """$VAR without braces is NOT replaced."""
        result = substitute_vars("echo $VAR", {"VAR": "value"})
        assert result == "echo $VAR"

    def test_empty_string(self):
        result = substitute_vars("", {"VAR": "value"})
        assert result == ""

    def test_var_with_underscores(self):
        result = substitute_vars("${MY_VAR_NAME}", {"MY_VAR_NAME": "val"})
        assert result == "val"

    def test_var_with_digits(self):
        result = substitute_vars("${VAR1}", {"VAR1": "one"})
        assert result == "one"

    def test_repeated_var(self):
        result = substitute_vars("${X} and ${X}", {"X": "y"})
        assert result == "y and y"


class TestWarnSuspiciousVars:
    """Suspicious pattern detection in variable values."""

    def test_semicolon_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            warn_suspicious_vars({"CMD": "echo; rm -rf /"})
        assert "suspicious" in caplog.text.lower()

    def test_double_ampersand_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            warn_suspicious_vars({"CMD": "echo && rm -rf"})
        assert "suspicious" in caplog.text.lower()

    def test_pipe_or_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            warn_suspicious_vars({"CMD": "echo || true"})
        assert "suspicious" in caplog.text.lower()

    def test_command_substitution_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            warn_suspicious_vars({"CMD": "$(whoami)"})
        assert "suspicious" in caplog.text.lower()

    def test_backtick_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            warn_suspicious_vars({"CMD": "`whoami`"})
        assert "suspicious" in caplog.text.lower()

    def test_newline_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            warn_suspicious_vars({"CMD": "echo\nrm -rf /"})
        assert "suspicious" in caplog.text.lower()

    def test_safe_value_no_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            warn_suspicious_vars({"PORT": "8080", "HOST": "localhost"})
        assert "suspicious" not in caplog.text.lower()

    def test_empty_vars_no_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            warn_suspicious_vars({})
        assert caplog.text == ""
