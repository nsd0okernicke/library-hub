"""Unit-Tests für das Isbn Value Object (Catalog Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: catalog.domain.isbn.Isbn

ISBN-10 und ISBN-13 werden gemäß ISO 2108 validiert:
- ISBN-13: 13 Ziffern, Prüfziffer mod 10 (Gewichte 1 und 3 abwechselnd)
- ISBN-10: 10 Zeichen, letzte kann 'X' sein, Prüfziffer mod 11
- Trennzeichen (Bindestriche) werden beim Parsen ignoriert.
"""

import pytest

from catalog.domain.isbn import Isbn


class TestIsbnCreation:
    """Tests für die Erzeugung eines Isbn Value Objects."""

    # ── ISBN-13 ──────────────────────────────────────────────────────────────

    def test_valid_isbn13_without_hyphens(self) -> None:
        """Gültige ISBN-13 ohne Bindestriche wird akzeptiert; str() gibt Ziffern zurück."""
        isbn = Isbn("9783161484100")
        assert isbn.digits == "9783161484100"
        assert str(isbn) == "9783161484100"  # kein Reformatting ohne Bindestrich-Info

    def test_valid_isbn13_with_hyphens(self) -> None:
        """Gültige ISBN-13 mit Bindestrichen – str() gibt original formatierten String zurück."""
        isbn = Isbn("978-3-16-148410-0")
        assert str(isbn) == "978-3-16-148410-0"

    def test_valid_isbn13_second_example(self) -> None:
        """Zweites gültiges ISBN-13-Beispiel."""
        isbn = Isbn("978-0-13-468599-1")
        assert str(isbn) == "978-0-13-468599-1"

    # ── ISBN-10 ──────────────────────────────────────────────────────────────

    def test_valid_isbn10_without_hyphens(self) -> None:
        """Gültige ISBN-10 ohne Bindestriche wird akzeptiert."""
        isbn = Isbn("0306406152")
        assert len(isbn.digits) == 10

    def test_valid_isbn10_with_hyphens(self) -> None:
        """Gültige ISBN-10 mit Bindestrichen wird akzeptiert."""
        isbn = Isbn("0-306-40615-2")
        assert len(isbn.digits) == 10

    def test_valid_isbn10_with_x_check_digit(self) -> None:
        """Gültige ISBN-10 mit Prüfziffer X wird akzeptiert."""
        isbn = Isbn("0-19-853453-1")
        assert isbn is not None

    # ── Ungültige Eingaben ───────────────────────────────────────────────────

    def test_invalid_isbn_wrong_length_raises(self) -> None:
        """ISBN mit falscher Länge (nicht 10 oder 13 Ziffern) wirft ValueError."""
        with pytest.raises(ValueError, match="[Ii][Ss][Bb][Nn]"):
            Isbn("12345")

    def test_invalid_isbn13_wrong_check_digit_raises(self) -> None:
        """ISBN-13 mit falscher Prüfziffer wirft ValueError."""
        with pytest.raises(ValueError, match="[Ii][Ss][Bb][Nn]|check"):
            Isbn("9783161484101")  # letzte Ziffer geändert: 0→1

    def test_invalid_isbn10_wrong_check_digit_raises(self) -> None:
        """ISBN-10 mit falscher Prüfziffer wirft ValueError."""
        with pytest.raises(ValueError, match="[Ii][Ss][Bb][Nn]|check"):
            Isbn("0306406153")  # letzte Ziffer geändert: 2→3

    def test_empty_string_raises(self) -> None:
        """Leerer String wirft ValueError."""
        with pytest.raises(ValueError, match="[Ii][Ss][Bb][Nn]"):
            Isbn("")

    def test_non_numeric_characters_raise(self) -> None:
        """Nicht-numerische Zeichen (außer Bindestriche) werfen ValueError."""
        with pytest.raises(ValueError, match="[Ii][Ss][Bb][Nn]"):
            Isbn("97831614841AB")


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
        isbn_a = Isbn("978-3-16-148410-0")
        isbn_b = Isbn("9783161484100")
        isbn_c = Isbn("978-0-13-468599-1")
        isbn_set = {isbn_a, isbn_b, isbn_c}
        assert len(isbn_set) == 2

    def test_isbn_is_immutable(self) -> None:
        """Isbn-Objekt ist unveränderlich (Value Object)."""
        isbn = Isbn("978-3-16-148410-0")
        with pytest.raises((AttributeError, TypeError)):
            isbn.digits = "0000000000000"  # type: ignore[misc]

    def test_isbn_str_returns_formatted_string(self) -> None:
        """str(isbn) gibt den formatierten ISBN-String zurück."""
        isbn = Isbn("9783161484100")
        assert isinstance(str(isbn), str)
        assert "9783161484100".replace("-", "") in str(isbn).replace("-", "")

    def test_isbn_repr_contains_value(self) -> None:
        """repr(isbn) enthält die ISBN-Nummer."""
        isbn = Isbn("978-3-16-148410-0")
        assert "978" in repr(isbn)

    def test_isbn_not_equal_to_plain_string(self) -> None:
        """Isbn ist nicht gleich einem plain str."""
        isbn = Isbn("978-3-16-148410-0")
        assert isbn != "978-3-16-148410-0"

    def test_isbn_digits_property_returns_only_digits(self) -> None:
        """digits-Property gibt nur die Ziffern ohne Bindestriche zurück."""
        isbn = Isbn("978-3-16-148410-0")
        assert isbn.digits == "9783161484100"
        assert "-" not in isbn.digits

