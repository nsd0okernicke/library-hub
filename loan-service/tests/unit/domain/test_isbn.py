"""Unit tests for the Isbn value object (Loan Service).

🔴 RED phase: These tests must FAIL before any implementation exists.
Tested class: loan.domain.isbn.Isbn

ISBN-10 and ISBN-13 are validated according to ISO 2108:
- ISBN-13: 13 digits, check digit mod 10 (alternating weights 1 and 3)
- ISBN-10: 10 characters, last may be 'X', check digit mod 11
- Separator hyphens are stripped before validation.
"""

import pytest

from loan.domain.isbn import Isbn


class TestIsbnCreation:
    """Tests for creating an Isbn value object."""

    def test_valid_isbn13_without_hyphens(self) -> None:
        """Valid ISBN-13 without hyphens; str() returns the digit string."""
        isbn = Isbn("9783161484100")
        assert isbn.digits == "9783161484100"
        assert str(isbn) == "9783161484100"

    def test_valid_isbn13_with_hyphens(self) -> None:
        """Valid ISBN-13 with hyphens – str() returns the original formatted string."""
        isbn = Isbn("978-3-16-148410-0")
        assert str(isbn) == "978-3-16-148410-0"

    def test_valid_isbn10_without_hyphens(self) -> None:
        """Valid ISBN-10 without hyphens is accepted."""
        isbn = Isbn("0306406152")
        assert len(isbn.digits) == 10

    def test_valid_isbn10_with_hyphens(self) -> None:
        """Valid ISBN-10 with hyphens is accepted."""
        isbn = Isbn("0-306-40615-2")
        assert len(isbn.digits) == 10

    def test_valid_isbn10_with_x_check_digit(self) -> None:
        """ISBN-10 with 'X' as check digit is accepted (X=10, not 11)."""
        isbn = Isbn("080442957X")
        assert isbn.digits == "080442957X"

    def test_isbn10_x_value_is_10_not_11(self) -> None:
        """X has value 10 (not 11) – if it were 11, 080442957X would be incorrectly rejected."""
        assert Isbn("080442957X") is not None

    def test_isbn10_lowercase_x_is_rejected(self) -> None:
        """Lowercase 'x' is invalid."""
        with pytest.raises(ValueError):
            Isbn("047196436x")

    def test_empty_string_raises_with_message(self) -> None:
        """Empty string raises ValueError – message starts with 'ISBN must not be empty'."""
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
        """Non-numeric characters raise ValueError containing 'invalid characters'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("97831614841AB")
        msg = str(exc_info.value)
        assert "invalid characters" in msg
        assert msg.startswith("ISBN")
        assert not msg.startswith("XX")

    def test_invalid_isbn13_wrong_check_digit_raises_with_message(self) -> None:
        """ISBN-13 with wrong check digit raises ValueError containing 'invalid check digit'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("9783161484101")
        msg = str(exc_info.value)
        assert "invalid check digit" in msg
        assert not msg.startswith("XX")

    def test_invalid_isbn10_wrong_check_digit_raises_with_message(self) -> None:
        """ISBN-10 with wrong check digit – message starts with 'ISBN-10' (not 'XX')."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("0306406153")
        msg = str(exc_info.value)
        assert msg.startswith("ISBN-10")
        assert "invalid check digit" in msg
        assert not msg.startswith("XX")

    def test_isbn10_accumulation_is_addition_not_subtraction(self) -> None:
        """ISBN-10 checksum uses += not -= (kill += → -= mutant).

        With subtraction the weighted sum for 0306406152 would be negative and
        not divisible by 11, so the valid ISBN would be incorrectly rejected.
        """
        isbn = Isbn("0-306-40615-2")
        assert isbn.digits == "0306406152"
        with pytest.raises(ValueError) as exc_info:
            Isbn("0-306-40615-1")
        assert "invalid check digit" in str(exc_info.value)
        # Second valid ISBN-10 further constrains the arithmetic direction
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
        a = Isbn("978-3-16-148410-0")
        b = Isbn("9783161484100")
        c = Isbn("978-0-13-468599-1")
        assert len({a, b, c}) == 2

    def test_isbn_is_immutable(self) -> None:
        """Isbn object is immutable – setting attributes raises AttributeError."""
        isbn = Isbn("978-3-16-148410-0")
        with pytest.raises(AttributeError) as exc_info:
            isbn.digits = "0000000000000"  # type: ignore[misc]
        msg = str(exc_info.value)
        assert "immutable" in msg
        # kill mutant: error message must NOT be wrapped in XX...XX
        assert "XX" not in msg

    def test_isbn_repr_starts_with_isbn_class_name(self) -> None:
        """repr(isbn) starts with 'Isbn(' – no 'XX' prefix."""
        isbn = Isbn("978-3-16-148410-0")
        r = repr(isbn)
        assert r.startswith("Isbn(")
        assert "XX" not in r

    def test_isbn_digits_property_returns_only_digits(self) -> None:
        """digits property returns only the digit string without hyphens."""
        isbn = Isbn("978-3-16-148410-0")
        assert isbn.digits == "9783161484100"
        assert "-" not in isbn.digits

    def test_isbn_not_equal_to_plain_string(self) -> None:
        """Isbn is not equal to a plain string."""
        assert Isbn("978-3-16-148410-0") != "978-3-16-148410-0"

