import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def test_user_password() -> str:
    return "SecretPassword"


@pytest_asyncio.fixture
async def test_user(
    db_session: AsyncSession,
    test_user_password: str,
) -> User:
    user = User(
        email="testuser@example.com",
        password_hash=get_password_hash(test_user_password),
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def inactive_test_user(
    db_session: AsyncSession,
    test_user_password: str,
) -> User:
    user = User(
        email="inactive@example.com",
        password_hash=get_password_hash(test_user_password),
        is_active=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


def get_auth_headers(user: User) -> dict[str, str]:
    access_token = create_access_token(
        subject=str(user.id)
    )

    return {
        "Authorization": f"Bearer {access_token}"
    }


class TestChangePassword:

    async def test_change_password_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_password: str,
    ):
        payload = {
            "old_password": test_user_password,
            "new_password": "NewSecretPassword",
        }

        response = await async_client.post(
            "/api/v1/users/me/change-password",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_change_password_same_as_old(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_password: str,
    ):
        payload = {
            "old_password": test_user_password,
            "new_password": test_user_password,
        }

        response = await async_client.post(
            "/api/v1/users/me/change-password",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_change_password_invalid_old_password(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        payload = {
            "old_password": "WrongPassword",
            "new_password": "NewSecretPassword",
        }

        response = await async_client.post(
            "/api/v1/users/me/change-password",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_change_password_missing_body(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.post(
            "/api/v1/users/me/change-password",
            headers=get_auth_headers(test_user),
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_change_password_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
        test_user_password: str,
    ):
        payload = {
            "old_password": test_user_password,
            "new_password": "NewSecretPassword",
        }

        response = await async_client.post(
            "/api/v1/users/me/change-password",
            headers=get_auth_headers(inactive_test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteCurrentUser:

    async def test_delete_current_user_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        response = await async_client.delete(
            "/api/v1/users/me",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        result = await db_session.execute(
            select(User).where(User.id == test_user.id)
        )

        deleted_user = result.scalar_one_or_none()

        assert deleted_user is None

    async def test_access_after_user_deletion(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        headers = get_auth_headers(test_user)

        response = await async_client.delete(
            "/api/v1/users/me",
            headers=headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = await async_client.get(
            "/api/v1/users/me",
            headers=headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_current_user_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
    ):
        response = await async_client.delete(
            "/api/v1/users/me",
            headers=get_auth_headers(inactive_test_user),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN