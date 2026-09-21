import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core.security import get_password_hash, create_access_token, create_refresh_token


@pytest.fixture
def test_user_password() -> str:
    return "SecretPassword"


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_password: str) -> User:
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
async def inactive_test_user(db_session: AsyncSession, test_user_password: str) -> User:
    user = User(
        email="inactive@example.com",
        password_hash=get_password_hash(test_user_password),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
class TestRegisterEndpoint:
    async def test_register_user_success(self, async_client: AsyncClient):
        payload = {
            "email" : "newuser@example.com",
            "password" : "SecretPassword"
        }

        response = await async_client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user: User):
        payload = {
            "email" : "testuser@example.com",
            "password" : "SecretPassword"
        }

        response = await async_client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_register_duplicate_username(self, async_client: AsyncClient, test_user: User):
        payload = {
            "email" : "newuser@example.com",
            "password" : "SecretPassword"
        }

        response = await async_client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_register_invalid_email(self, async_client: AsyncClient):
        payload = {
            "email" : "invalid_email",
            "password" : "SecretPassword"
        }

        response = await async_client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_register_invalid_username(self, async_client: AsyncClient):
            payload = {
                "email" : "newuser@example.com",
                "password" : "SecretPassword"
            }
    
            response = await async_client.post("/api/v1/auth/register", json=payload)
    
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT



@pytest.mark.asyncio
class TestLoginEndpoint:

    async def test_login_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_user_password: str,
    ):
        payload = {
            "email": test_user.email,
            "password": test_user_password,
        }

        response = await async_client.post(
            "/api/v1/auth/login",
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        payload = {
            "email": test_user.email,
            "password": "WrongPassword",
        }

        response = await async_client.post(
            "/api/v1/auth/login",
            json=payload,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_nonexistent_user(
        self,
        async_client: AsyncClient,
    ):
        payload = {
            "email": "nonexistent@example.com",
            "password": "SecretPassword",
        }

        response = await async_client.post(
            "/api/v1/auth/login",
            json=payload,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
        test_user_password: str,
    ):
        payload = {
            "email": inactive_test_user.email,
            "password": test_user_password,
        }

        response = await async_client.post(
            "/api/v1/auth/login",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
class TestRefreshEndpoint:

    async def test_refresh_success(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        refresh_token = create_refresh_token(
            subject=str(test_user.id)
        )

        payload = {
            "refresh_token": refresh_token,
        }

        response = await async_client.post(
            "/api/v1/auth/refresh",
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_invalid_token(
        self,
        async_client: AsyncClient,
    ):
        payload = {
            "refresh_token": "invalid-refresh-token",
        }

        response = await async_client.post(
            "/api/v1/auth/refresh",
            json=payload,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
    ):
        refresh_token = create_refresh_token(
            subject=str(inactive_test_user.id)
        )

        payload = {
            "refresh_token": refresh_token,
        }

        response = await async_client.post(
            "/api/v1/auth/refresh",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN