"""Variable substitution for procler commands.

Replaces ${VAR} patterns in commands with values from config.vars.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Patterns that might indicate shell injection
SUSPICIOUS_PATTERNS = [";", "&&", "||", "$(", "`", "\n"]


def warn_suspicious_vars(vars: dict[str, str]) -> None:
    """Log warnings for vars containing suspicious patterns."""
    for name, value in vars.items():
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in value:
                logger.warning(
                    f"Variable '{name}' contains suspicious pattern '{pattern}'. Ensure this is intentional."
                )
                break


def substitute_vars(text: str, vars: dict[str, str]) -> str:
    """
    Replace ${VAR} patterns with values from vars dict.

    If a variable is not found, the original ${VAR} pattern is kept.

    Args:
        text: String containing ${VAR} patterns
        vars: Dict mapping variable names to values

    Returns:
        String with variables substituted
    """
    if not vars:
        return text

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in vars:
            return vars[var_name]
        # Keep original if not found
        return match.group(0)

    # Match ${VAR_NAME} pattern (alphanumeric and underscore)
    return re.sub(r"\$\{(\w+)\}", replacer, text)


def substitute_vars_from_config(text: str) -> str:
    """
    Replace ${VAR} patterns with values from config.vars.

    Convenience function that loads vars from the current config.
    """
    # Import here to avoid circular dependency
    from procler.config.loader import get_config

    config = get_config()
    return substitute_vars(text, config.vars)
