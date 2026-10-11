"""Environment identifiers (stdlib only — no config imports)."""

from __future__ import annotations

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class EnvType(Enum):
    """Deployment environment with a canonical key and case-insensitive aliases.

    ``value`` is the canonical config key (for example ``stg``). Extra strings
    in each member's tuple are aliases (for example ``staging``). Enum names
    such as ``STAGING`` are also accepted by :meth:`from_string` and
    :meth:`equals`.

    Examples
    --------
    >>> EnvType.from_string("staging") is EnvType.STAGING
    True
    >>> EnvType.PROD.equals("production")
    True
    >>> EnvType.DEV.equals_any(["qa", "prod"])
    False
    """

    LOCAL = ("local",)
    DEV = ("dev", "develop", "development")
    PROD = ("prod", "production", "live")
    QA = ("qa",)
    STAGING = ("stg", "stage", "staging")
    TEST = ("test", "testing")
    UAT = ("uat",)

    def __new__(cls, env_key: str, *aliases: str) -> EnvType:
        """Create a member whose ``value`` is ``env_key`` and store all aliases.

        The canonical key is included in the alias set so lookups can use a
        single membership test.
        """
        member = object.__new__(cls)
        member._value_ = env_key
        member._aliases = frozenset(
            {env_key.lower(), *(alias.lower() for alias in aliases)}
        )
        return member

    @property
    def env_type(self) -> str:
        """Canonical environment key (same as ``.value``), e.g. ``stg``."""
        return self.value

    @property
    def aliases(self) -> frozenset[str]:
        """Lowercased strings recognized for this member, including the canonical key."""
        return self._aliases

    @classmethod
    def from_string(cls, env_type: EnvType | str | None) -> EnvType | None:
        """Parse a config key, alias, or enum name into an :class:`EnvType`.

        Accepts values such as ``stg``, ``staging``, or ``STAGING``. Matching is
        case-insensitive. If ``env_type`` is already an :class:`EnvType`, it is
        returned unchanged.

        Logs and returns ``None`` when the value is empty, the wrong type, or
        unrecognized.
        """
        if isinstance(env_type, cls):
            return env_type

        if not isinstance(env_type, str) or not env_type.strip():
            logger.error(
                "Invalid environment: expected non-empty string, got %r",
                env_type,
            )
            return None

        key = env_type.strip().lower()
        for member in cls:
            if key in member._aliases or member.name.lower() == key:
                return member

        known = ", ".join(sorted(m.value for m in cls))
        logger.error(
            "Unknown Environment: %r. Expected a canonical key (%s), an alias, or an enum name.",
            env_type,
            known,
        )
        return None

    @classmethod
    def names(cls) -> list[str]:
        """Return all enum member names in definition order."""
        return [member.name for member in cls]

    def equals(self, other: object) -> bool:
        """Return True if ``other`` is this same environment.

        ``other`` may be an :class:`EnvType` member or a string (canonical key,
        alias, or enum name). Matching is case-insensitive. Empty or unknown
        values return False without treating them as a parse error for logging.
        """
        if isinstance(other, EnvType):
            return self is other
        if not isinstance(other, str) or not other.strip():
            return False

        normalized = other.strip().lower()
        return normalized in self._aliases or self.name.lower() == normalized

    def not_equals(self, other: object) -> bool:
        """Return True if ``other`` is not this environment."""
        return not self.equals(other)

    def equals_any(self, others: list[object]) -> bool:
        """Return True if this environment matches any value in ``others``."""
        return any(self.equals(item) for item in others)

    def not_equals_any(self, others: list[object]) -> bool:
        """Return True if this environment matches none of the values in ``others``."""
        return not self.equals_any(others)

    def __str__(self) -> str:
        """Return the canonical environment key."""
        return self.value
