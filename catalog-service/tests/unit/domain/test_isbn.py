"""Unit tests for the Isbn value object (Catalog Service).

Tested class: catalog.domain.isbn.Isbn

ISBN-10 and ISBN-13 are validated according to ISO 2108:
- ISBN-13: 13 digits, check digit mod 10 (alternating weights 1 and 3)
- ISBN-10: 10 characters, last may be 'X', check digit mod 11
- Separator hyphens are stripped before validation.
"""

import pytest

from catalog.domain.isbn import Isbn


class TestIsbnCreation:
    """Tests for creating an Isbn value object."""

    # ── ISBN-13 ───────────────────────────────────────────────────────────────

    def test_valid_isbn13_without_hyphens(self) -> None:
        """Valid ISBN-13 without hyphens is accepted; str() returns the digit string."""
        isbn = Isbn("9783161484100")
        assert isbn.digits == "9783161484100"
        assert str(isbn) == "9783161484100"

    def test_valid_isbn13_with_hyphens(self) -> None:
        """Valid ISBN-13 with hyphens – str() returns the original formatted string."""
        isbn = Isbn("978-3-16-148410-0")
        assert str(isbn) == "978-3-16-148410-0"

    def test_valid_isbn13_second_example(self) -> None:
        """Second valid ISBN-13 example."""
        isbn = Isbn("978-0-13-468599-1")
        assert str(isbn) == "978-0-13-468599-1"

    # ── ISBN-10 ───────────────────────────────────────────────────────────────

    def test_valid_isbn10_without_hyphens(self) -> None:
        """Valid ISBN-10 without hyphens is accepted."""
        isbn = Isbn("0306406152")
        assert len(isbn.digits) == 10

    def test_valid_isbn10_with_hyphens(self) -> None:
        """Valid ISBN-10 with hyphens is accepted."""
        isbn = Isbn("0-306-40615-2")
        assert len(isbn.digits) == 10

    def test_valid_isbn10_with_x_check_digit(self) -> None:
        """ISBN-10 with 'X' as check digit is correctly accepted (X=10, not 11)."""
        isbn = Isbn("080442957X")
        assert isbn.digits == "080442957X"

    def test_isbn10_x_value_is_10_in_checksum(self) -> None:
        """X has value 10 (not 11) – if 11, 080442957X would be incorrectly rejected."""
        # Control: valid ISBN-10 ending in X is accepted
        assert Isbn("080442957X") is not None
        # Control: valid ISBN-10 without X is also accepted
        isbn = Isbn("0-306-40615-2")
        assert isbn.digits == "0306406152"

    def test_isbn10_x_only_valid_at_last_position(self) -> None:
        """'X' in the middle of an ISBN-10 is rejected."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("04X196436Y")
        assert "contains invalid characters" in str(exc_info.value)

    def test_isbn13_x_is_never_valid(self) -> None:
        """'X' in an ISBN-13 is always invalid."""
        with pytest.raises(ValueError):
            Isbn("978-3-16-14841X-0")

    def test_isbn10_lowercase_x_is_rejected(self) -> None:
        """Lowercase 'x' (not 'X') is invalid."""
        with pytest.raises(ValueError):
            Isbn("047196436x")

    # ── Invalid inputs ────────────────────────────────────────────────────────

    def test_empty_string_raises_with_message(self) -> None:
        """Empty string raises ValueError with message starting with 'ISBN must not be empty'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("")
        assert str(exc_info.value).startswith("ISBN must not be empty")

    def test_invalid_isbn_wrong_length_raises_with_message(self) -> None:
        """ISBN with wrong length raises ValueError containing 'expected 10 or 13'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("12345")
        msg = str(exc_info.value)
        assert "expected 10 or 13" in msg
        assert not msg.startswith("XX")

    def test_non_numeric_characters_raise_with_message(self) -> None:
        """Non-numeric characters raise ValueError containing 'contains invalid characters'
        and the hint text starting with '(only digits'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("97831614841AB")
        msg = str(exc_info.value)
        assert "contains invalid characters" in msg
        assert "only digits" in msg
        # kill mutant: error text must NOT be wrapped in XX...XX
        assert not msg.startswith("XX")
        assert "XX" not in msg

    def test_invalid_isbn13_wrong_check_digit_raises_with_message(self) -> None:
        """ISBN-13 with wrong check digit raises ValueError with exact phrases."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("9783161484101")
        msg = str(exc_info.value)
        assert "invalid check digit" in msg
        assert "expected multiple of 10" in msg
        # kill mutant: error text must NOT be wrapped in XX...XX
        assert not msg.startswith("XX")
        assert "XX" not in msg

    def test_invalid_isbn10_wrong_check_digit_raises_with_message(self) -> None:
        """ISBN-10 with wrong check digit raises ValueError with exact phrases."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("0306406153")
        msg = str(exc_info.value)
        assert "invalid check digit" in msg
        assert "expected multiple of 11" in msg
        # kill mutant: error text must NOT be wrapped in XX...XX
        assert not msg.startswith("XX")
        assert "XX" not in msg

    def test_isbn10_accumulation_is_addition_not_subtraction(self) -> None:
        """ISBN-10 checksum uses += not -= (kill += → -= mutant).

        With subtraction the weighted sum for 0306406152 would be negative and
        not divisible by 11, so the valid ISBN would be incorrectly rejected.
        """
        # Valid ISBN-10 must be accepted – would fail with -= due to negative sum
        isbn = Isbn("0-306-40615-2")
        assert isbn.digits == "0306406152"
        # A neighbouring check digit must be rejected
        with pytest.raises(ValueError) as exc_info:
            Isbn("0-306-40615-1")
        assert "invalid check digit" in str(exc_info.value)
        # Second valid ISBN-10 to further constrain the arithmetic direction
        isbn2 = Isbn("0471958697")
        assert isbn2.digits == "0471958697"


class TestIsbnValueSemantics:
    """Tests for the value semantics of the Isbn value object."""

    def test_same_isbn_strings_are_equal(self) -> None:
        """Two Isbn objects with the same number are equal."""
        assert Isbn("978-3-16-148410-0") == Isbn("9783161484100")

    def test_different_isbn_strings_are_not_equal(self) -> None:
        """Two Isbn objects with different numbers are not equal."""
        assert Isbn("978-3-16-148410-0") != Isbn("978-0-13-468599-1")

    def test_isbn_is_hashable(self) -> None:
        """Isbn is hashable and can be stored in a set."""
        isbn_a = Isbn("978-3-16-148410-0")
        isbn_b = Isbn("9783161484100")
        isbn_c = Isbn("978-0-13-468599-1")
        isbn_set = {isbn_a, isbn_b, isbn_c}
        assert len(isbn_set) == 2

    def test_isbn_is_immutable(self) -> None:
        """Isbn object is immutable – __setattr__ raises AttributeError."""
        isbn = Isbn("978-3-16-148410-0")
        with pytest.raises(AttributeError) as exc_info:
            isbn.digits = "0000000000000"  # type: ignore[misc]
        assert "immutable" in str(exc_info.value)
        assert not str(exc_info.value).startswith("XX")

    def test_isbn_str_returns_formatted_string(self) -> None:
        """str(isbn) returns the formatted ISBN string."""
        isbn = Isbn("9783161484100")
        assert isinstance(str(isbn), str)
        assert "9783161484100".replace("-", "") in str(isbn).replace("-", "")

    def test_isbn_repr_starts_with_isbn_class_name(self) -> None:
        """repr(isbn) starts with 'Isbn(' – no 'XX' prefix."""
        isbn = Isbn("978-3-16-148410-0")
        r = repr(isbn)
        assert r.startswith("Isbn(")
        assert "XX" not in r

    def test_isbn_not_equal_to_plain_string(self) -> None:
        """Isbn is not equal to a plain string."""
        isbn = Isbn("978-3-16-148410-0")
        assert isbn != "978-3-16-148410-0"

    def test_isbn_digits_property_returns_only_digits(self) -> None:
        """digits property returns only the digit string without hyphens."""
        isbn = Isbn("978-3-16-148410-0")
        assert isbn.digits == "9783161484100"
        assert "-" not in isbn.digits

