"""Use case: retrieve a user by e-mail address (Loan Service)."""
from loan.domain.ports.user_repository import UserRepository
from loan.domain.user import User


class GetUserByEmailUseCase:
    """Look up a registered user by e-mail address.

    Args:
        user_repo: Repository used to query user data.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, email: str) -> User:
        """Return the user with the given e-mail address.

        Args:
            email: The e-mail address to look up.

        Returns:
            The matching User domain object.

        Raises:
            ValueError: If no user with that e-mail address exists.
        """
        user = await self._user_repo.find_by_email(email)
        if user is None:
            raise ValueError(f"No user found for e-mail: {email}")
        return user

