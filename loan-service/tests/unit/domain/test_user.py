"""Unit-Tests für das User-Domain-Modell (Loan Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: loan.domain.user.User
"""

import uuid

import pytest

from loan.domain.user import User


class TestUserCreation:
    """Tests für die Erzeugung eines User-Domänenobjekts."""

    def test_create_user_with_all_fields(self) -> None:
        """User kann mit allen Feldern erzeugt werden."""
        user_id = uuid.uuid4()
        user = User(id=user_id, name="Alice Müller", email="alice@example.com")
        assert user.id == user_id
        assert user.name == "Alice Müller"
        assert user.email == "alice@example.com"

    def test_create_user_without_id_generates_uuid(self) -> None:
        """Wird keine ID angegeben, wird automatisch eine UUID generiert."""
        user = User(name="Bob Schmidt", email="bob@example.com")
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)

    def test_two_users_with_same_id_are_equal(self) -> None:
        """Zwei User mit gleicher ID gelten als gleich."""
        uid = uuid.uuid4()
        user_a = User(id=uid, name="Alice", email="alice@example.com")
        user_b = User(id=uid, name="Different Name", email="other@example.com")
        assert user_a == user_b

    def test_two_users_with_different_id_are_not_equal(self) -> None:
        """Zwei User mit unterschiedlicher ID gelten nicht als gleich."""
        user_a = User(name="Alice", email="alice@example.com")
        user_b = User(name="Alice", email="alice@example.com")
        assert user_a != user_b

    def test_user_email_must_not_be_empty(self) -> None:
        """Leere E-Mail ist nicht erlaubt."""
        with pytest.raises((ValueError, Exception)):
            User(name="Alice", email="")

    def test_user_name_must_not_be_empty(self) -> None:
        """Leerer Name ist nicht erlaubt."""
        with pytest.raises((ValueError, Exception)):
            User(name="", email="alice@example.com")

    def test_user_not_equal_to_non_user(self) -> None:
        """User verglichen mit einem Nicht-User gibt NotImplemented zurück."""
        user = User(name="Alice", email="alice@example.com")
        assert user.__eq__("not-a-user") is NotImplemented

    def test_user_hashable_and_usable_in_set(self) -> None:
        """User ist hashbar und kann in einem Set verwendet werden."""
        import uuid as _uuid
        uid = _uuid.uuid4()
        user_a = User(id=uid, name="Alice", email="alice@example.com")
        user_b = User(id=uid, name="Alice Copy", email="copy@example.com")
        user_c = User(name="Bob", email="bob@example.com")
        user_set = {user_a, user_b, user_c}
        assert len(user_set) == 2

    def test_user_repr_contains_id_and_email(self) -> None:
        """__repr__ enthält id und email."""
        user = User(name="Alice", email="alice@example.com")
        representation = repr(user)
        assert "alice@example.com" in representation

