"""Unit-Tests für das Isbn Value Object (Loan Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: loan.domain.isbn.Isbn

ISBN-10 und ISBN-13 werden gemäß ISO 2108 validiert:
- ISBN-13: 13 Ziffern, Prüfziffer mod 10 (Gewichte 1 und 3 abwechselnd)
- ISBN-10: 10 Zeichen, letzte kann 'X' sein, Prüfziffer mod 11
- Trennzeichen (Bindestriche) werden beim Parsen ignoriert.
"""

import pytest

from loan.domain.isbn import Isbn


class TestIsbnCreation:
    """Tests für die Erzeugung eines Isbn Value Objects."""

    def test_valid_isbn13_without_hyphens(self) -> None:
        """Gültige ISBN-13 ohne Bindestriche; str() gibt Ziffern zurück."""
        isbn = Isbn("9783161484100")
        assert isbn.digits == "9783161484100"
        assert str(isbn) == "9783161484100"

    def test_valid_isbn13_with_hyphens(self) -> None:
        """Gültige ISBN-13 mit Bindestrichen – str() gibt original formatierten String zurück."""
        isbn = Isbn("978-3-16-148410-0")
        assert str(isbn) == "978-3-16-148410-0"

    def test_valid_isbn10_without_hyphens(self) -> None:
        """Gültige ISBN-10 ohne Bindestriche wird akzeptiert."""
        isbn = Isbn("0306406152")
        assert len(isbn.digits) == 10

    def test_valid_isbn10_with_hyphens(self) -> None:
        """Gültige ISBN-10 mit Bindestrichen wird akzeptiert."""
        isbn = Isbn("0-306-40615-2")
        assert len(isbn.digits) == 10

    def test_valid_isbn10_with_x_check_digit(self) -> None:
        """ISBN-10 mit 'X' als Prüfziffer wird akzeptiert (X=10, nicht 11)."""
        isbn = Isbn("080442957X")
        assert isbn.digits == "080442957X"

    def test_isbn10_x_value_is_10_not_11(self) -> None:
        """X hat Wert 10 (nicht 11) – wenn 11, würde 080442957X fälschlich abgelehnt."""
        assert Isbn("080442957X") is not None

    def test_isbn10_lowercase_x_is_rejected(self) -> None:
        """Kleingeschriebenes 'x' ist ungültig."""
        with pytest.raises(ValueError):
            Isbn("047196436x")

    def test_empty_string_raises_with_message(self) -> None:
        """Leerer String wirft ValueError – Meldung beginnt mit 'ISBN must not be empty'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("")
        assert str(exc_info.value).startswith("ISBN must not be empty")

    def test_invalid_isbn_wrong_length_raises_with_message(self) -> None:
        """ISBN mit falscher Länge wirft ValueError mit 'expected 10 or 13'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("12345")
        msg = str(exc_info.value)
        assert "expected 10 or 13" in msg
        assert not msg.startswith("XX")

    def test_non_numeric_characters_raise_with_message(self) -> None:
        """Nicht-numerische Zeichen werfen ValueError mit 'invalid characters'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("97831614841AB")
        msg = str(exc_info.value)
        assert "invalid characters" in msg
        assert msg.startswith("ISBN")
        assert not msg.startswith("XX")

    def test_invalid_isbn13_wrong_check_digit_raises_with_message(self) -> None:
        """ISBN-13 mit falscher Prüfziffer wirft ValueError mit 'invalid check digit'."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("9783161484101")
        msg = str(exc_info.value)
        assert "invalid check digit" in msg
        assert not msg.startswith("XX")

    def test_invalid_isbn10_wrong_check_digit_raises_with_message(self) -> None:
        """ISBN-10 mit falscher Prüfziffer – Meldung beginnt mit 'ISBN-10' (nicht 'XX')."""
        with pytest.raises(ValueError) as exc_info:
            Isbn("0306406153")
        msg = str(exc_info.value)
        assert msg.startswith("ISBN-10")
        assert "invalid check digit" in msg
        assert not msg.startswith("XX")

    def test_isbn10_accumulation_is_addition_not_subtraction(self) -> None:
        """ISBN-10 Prüfsumme wird mit += berechnet (nicht -=)."""
        isbn = Isbn("0-306-40615-2")
        assert isbn.digits == "0306406152"
        with pytest.raises(ValueError) as exc_info:
            Isbn("0-306-40615-1")
        assert "invalid check digit" in str(exc_info.value)


class TestIsbnValueSemantics:
    """Tests für die Wert-Semantik des Isbn Value Objects."""

    def test_same_isbn_strings_are_equal(self) -> None:
        """Zwei Isbn-Objekte mit gleicher Nummer sind gleich."""
        assert Isbn("978-3-16-148410-0") == Isbn("9783161484100")

    def test_different_isbn_strings_are_not_equal(self) -> None:
        """Zwei Isbn-Objekte mit unterschiedlichen Nummern sind ungleich."""
        assert Isbn("978-3-16-148410-0") != Isbn("978-0-13-468599-1")

    def test_isbn_is_hashable(self) -> None:
        """Isbn ist hashbar und kann in einem Set verwendet werden."""
        a = Isbn("978-3-16-148410-0")
        b = Isbn("9783161484100")
        c = Isbn("978-0-13-468599-1")
        assert len({a, b, c}) == 2

    def test_isbn_is_immutable(self) -> None:
        """Isbn-Objekt ist unveränderlich – kein Setzen von Attributen möglich."""
        isbn = Isbn("978-3-16-148410-0")
        with pytest.raises(AttributeError):
            isbn.digits = "0000000000000"  # type: ignore[misc]

    def test_isbn_repr_starts_with_isbn_class_name(self) -> None:
        """repr(isbn) beginnt mit 'Isbn(' – kein 'XX'-Präfix."""
        isbn = Isbn("978-3-16-148410-0")
        r = repr(isbn)
        assert r.startswith("Isbn(")
        assert "XX" not in r

    def test_isbn_digits_property_returns_only_digits(self) -> None:
        """digits-Property gibt nur die Ziffern ohne Bindestriche zurück."""
        isbn = Isbn("978-3-16-148410-0")
        assert isbn.digits == "9783161484100"
        assert "-" not in isbn.digits

    def test_isbn_not_equal_to_plain_string(self) -> None:
        """Isbn ist nicht gleich einem plain str."""
        assert Isbn("978-3-16-148410-0") != "978-3-16-148410-0"

