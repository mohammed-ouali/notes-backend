from app.core.exceptions import (
    InvalidPasswordException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.core.security import get_password_hash, verify_password
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user_by_id(
        self,
        user_id: int,
    ) -> User:

        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundException(
                f"User with ID {user_id} not found"
            )

        return user

    async def create_user(
        self,
        user_data: UserCreate,
    ) -> User:

        if await self.repository.get_by_email(user_data.email):
            raise UserAlreadyExistsException(
                "Email is already registered"
            )

        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            is_active=True,
        )

        return await self.repository.create(user)

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> None:

        user = await self.get_user_by_id(user_id)

        if not verify_password(old_password, user.password_hash):
            raise InvalidPasswordException("Current password is incorrect")

        user.password_hash = get_password_hash(new_password)

        await self.repository.update(user)

    async def delete_user(
        self,
        user_id: int,
    ) -> None:

        user = await self.get_user_by_id(user_id)

        await self.repository.delete(user)