from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()


    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        statement = select(User).where(
            User.email == email
        )

        result = await self.db.execute(statement)

        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)

        await self.db.commit()