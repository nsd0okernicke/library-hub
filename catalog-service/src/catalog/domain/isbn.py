"""Domain value object: Isbn (Catalog Service).

Validates and represents an ISBN-10 or ISBN-13 according to ISO 2108.
"""

from __future__ import annotations


class Isbn:
    """Immutable value object representing a validated ISBN-10 or ISBN-13.

    Hyphens in the input are stripped before validation. The internal
    representation always stores the raw digits only. The formatted string
    (with hyphens as provided, or digits-only if no hyphens were given) is
    preserved for display purposes.

    Attributes:
        digits: The raw digit string (10 or 13 characters, no hyphens).

    Raises:
        ValueError: If the value is not a valid ISBN-10 or ISBN-13.

    Examples:
        >>> Isbn("978-3-16-148410-0")
        Isbn('978-3-16-148410-0')
        >>> Isbn("9783161484100").digits
        '9783161484100'
    """

    __slots__ = ("_digits", "_formatted")

    def __init__(self, value: str) -> None:
        """Initialise and validate an ISBN.

        Args:
            value: Raw ISBN string, hyphens allowed (e.g. '978-3-16-148410-0').

        Raises:
            ValueError: If the ISBN is not valid.
        """
        if not value:
            raise ValueError("ISBN must not be empty")

        digits = value.replace("-", "")

        if not digits.replace("X", "").isdigit():
            raise ValueError(
                f"ISBN '{value}' contains invalid characters "
                "(only digits and hyphens; 'X' allowed as last char of ISBN-10)"
            )

        if len(digits) == 13:
            _validate_isbn13(digits)
        elif len(digits) == 10:
            _validate_isbn10(digits)
        else:
            raise ValueError(
                f"ISBN '{value}' has {len(digits)} digits; expected 10 or 13"
            )

        object.__setattr__(self, "_digits", digits)
        object.__setattr__(self, "_formatted", value)

    # ── Public API ───────────────────────────────────────────────────────────

    @property
    def digits(self) -> str:
        """Return the raw digits (no hyphens).

        Returns:
            10- or 13-character digit string.
        """
        return self._digits  # type: ignore[return-value]

    # ── Value object protocol ────────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        """Equality based on raw digits only."""
        if not isinstance(other, Isbn):
            return NotImplemented
        return self._digits == other._digits  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        """Hash based on raw digits."""
        return hash(self._digits)

    def __str__(self) -> str:
        """Return the original formatted string (with hyphens if provided)."""
        return self._formatted  # type: ignore[return-value]

    def __repr__(self) -> str:
        """Unambiguous representation."""
        return f"Isbn({self._formatted!r})"  # type: ignore[attr-defined]

    def __setattr__(self, name: str, value: object) -> None:
        """Prevent mutation – Isbn is immutable."""
        raise AttributeError("Isbn is immutable")


# ── Private helpers ──────────────────────────────────────────────────────────


def _validate_isbn13(digits: str) -> None:
    """Validate an ISBN-13 check digit (ISO 2108).

    Weights alternate 1 and 3; the weighted sum mod 10 must equal 0.

    Args:
        digits: Exactly 13 digit characters.

    Raises:
        ValueError: If the check digit is wrong.
    """
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    if total % 10 != 0:
        raise ValueError(
            f"ISBN-13 '{digits}' has an invalid check digit "
            f"(weighted sum={total}, expected multiple of 10)"
        )


def _validate_isbn10(digits: str) -> None:
    """Validate an ISBN-10 check digit (ISO 2108).

    Each digit is multiplied by its 1-based position; the last character may
    be 'X' (value 10). The weighted sum mod 11 must equal 0.

    Args:
        digits: Exactly 10 characters (digits or trailing 'X').

    Raises:
        ValueError: If the check digit is wrong.
    """
    total = 0
    for i, char in enumerate(digits):
        value = 10 if char.upper() == "X" else int(char)
        total += value * (i + 1)
    if total % 11 != 0:
        raise ValueError(
            f"ISBN-10 '{digits}' has an invalid check digit "
            f"(weighted sum={total}, expected multiple of 11)"
        )
