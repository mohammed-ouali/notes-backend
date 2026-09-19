import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models import Folder, Note, User


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
        username="test_user",
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
        username="inactive_user",
        is_active=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def other_test_user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="other@example.com",
        password_hash=get_password_hash("SecretPassword"),
        username="other_user",
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_folder(
    db_session: AsyncSession,
    test_user: User,
) -> Folder:
    folder = Folder(
        user_id=test_user.id,
        name="Test Folder",
    )

    db_session.add(folder)
    await db_session.commit()
    await db_session.refresh(folder)

    return folder


@pytest_asyncio.fixture
async def test_note(
    db_session: AsyncSession,
    test_user: User,
) -> Note:
    note = Note(
        user_id=test_user.id,
        title="Test Note",
        content="Test content",
    )

    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)

    return note


def get_auth_headers(user: User) -> dict[str, str]:
    access_token = create_access_token(
        subject=str(user.id)
    )

    return {
        "Authorization": f"Bearer {access_token}"
    }


class TestCreateNote:

    async def test_create_note_success(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        payload = {
            "title": "New Note",
            "content": "New note content",
        }

        response = await async_client.post(
            "/api/v1/notes",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["user_id"] == test_user.id
        assert data["title"] == payload["title"]
        assert data["content"] == payload["content"]
        assert data["folder_id"] is None

    async def test_create_note_without_auth(
        self,
        async_client: AsyncClient,
    ):
        payload = {
            "title": "New Note",
            "content": "New note content",
        }

        response = await async_client.post(
            "/api/v1/notes",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_note_invalid_title(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        payload = {
            "title": "   ",
            "content": "New note content",
        }

        response = await async_client.post(
            "/api/v1/notes",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_create_note_invalid_folder(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        payload = {
            "title": "New Note",
            "content": "New note content",
            "folder_id": 999999,
        }

        response = await async_client.post(
            "/api/v1/notes",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_note_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
    ):
        payload = {
            "title": "New Note",
            "content": "New note content",
        }

        response = await async_client.post(
            "/api/v1/notes",
            headers=get_auth_headers(inactive_test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetNotes:

    async def test_get_notes_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        first_note = Note(
            user_id=test_user.id,
            title="First Note",
            content="First content",
        )

        second_note = Note(
            user_id=test_user.id,
            title="Second Note",
            content="Second content",
        )

        db_session.add_all([first_note, second_note])
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/notes",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_get_notes_empty(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.get(
            "/api/v1/notes",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 0
        assert data["items"] == []

    async def test_get_notes_pagination(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        notes = [
            Note(
                user_id=test_user.id,
                title=f"Note {index}",
                content=f"Content {index}",
            )
            for index in range(3)
        ]

        db_session.add_all(notes)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/notes?page=1&limit=2",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 2

    async def test_get_notes_search(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        matching_note = Note(
            user_id=test_user.id,
            title="Python Backend",
            content="FastAPI project",
        )

        other_note = Note(
            user_id=test_user.id,
            title="Database",
            content="PostgreSQL project",
        )

        db_session.add_all([matching_note, other_note])
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/notes?q=Python",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["title"] == "Python Backend"

    async def test_get_notes_sorting(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        first_note = Note(
            user_id=test_user.id,
            title="First Note",
            content="First content",
        )

        db_session.add(first_note)
        await db_session.commit()

        second_note = Note(
            user_id=test_user.id,
            title="Second Note",
            content="Second content",
        )

        db_session.add(second_note)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/notes?sort_by=created_at&order=desc",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "Second Note"

    async def test_get_notes_folder_filter(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_folder: Folder,
    ):
        folder_note = Note(
            user_id=test_user.id,
            folder_id=test_folder.id,
            title="Folder Note",
            content="Inside folder",
        )

        other_note = Note(
            user_id=test_user.id,
            title="Other Note",
            content="Outside folder",
        )

        db_session.add_all([folder_note, other_note])
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/notes?folder_id={test_folder.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["title"] == "Folder Note"


class TestGetNote:

    async def test_get_note_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == test_note.id
        assert data["user_id"] == test_user.id
        assert data["title"] == test_note.title
        assert data["content"] == test_note.content

    async def test_get_note_not_found(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.get(
            "/api/v1/notes/999999",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_other_users_note(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        other_test_user: User,
        test_user: User,
    ):
        note = Note(
            user_id=other_test_user.id,
            title="Private Note",
            content="Private content",
        )

        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await async_client.get(
            f"/api/v1/notes/{note.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateNote:

    async def test_update_note_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        payload = {
            "title": "Updated Title",
            "content": "Updated content",
        }

        response = await async_client.put(
            f"/api/v1/notes/{test_note.id}",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["title"] == payload["title"]
        assert data["content"] == payload["content"]

    async def test_update_note_empty_body(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.put(
            f"/api/v1/notes/{test_note.id}",
            headers=get_auth_headers(test_user),
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_update_note_invalid_folder(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        payload = {
            "folder_id": 999999,
        }

        response = await async_client.put(
            f"/api/v1/notes/{test_note.id}",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_other_users_note(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        other_test_user: User,
        test_user: User,
    ):
        note = Note(
            user_id=other_test_user.id,
            title="Private Note",
            content="Private content",
        )

        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await async_client.put(
            f"/api/v1/notes/{note.id}",
            headers=get_auth_headers(test_user),
            json={
                "title": "Hacked",
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteNote:

    async def test_delete_note_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.delete(
            f"/api/v1/notes/{test_note.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_note_not_found(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.delete(
            "/api/v1/notes/999999",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_other_users_note(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        other_test_user: User,
        test_user: User,
    ):
        note = Note(
            user_id=other_test_user.id,
            title="Private Note",
            content="Private content",
        )

        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        response = await async_client.delete(
            f"/api/v1/notes/{note.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND