from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        offset: int,
        limit: int,
        q: str | None = None,
        sort_by: str = "username",
        order: str = "asc",
    ) -> tuple[list[User], int]:

        query = select(User)

        if q:
            query = query.where(
                User.username.ilike(f"%{q}%")
            )

        count_query = select(func.count()).select_from(
            query.subquery()
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        sort_column = getattr(User, sort_by, User.username)

        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

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