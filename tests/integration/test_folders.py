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


def get_auth_headers(user: User) -> dict[str, str]:
    access_token = create_access_token(
        subject=str(user.id)
    )

    return {
        "Authorization": f"Bearer {access_token}"
    }


class TestCreateFolder:

    async def test_create_folder_success(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        payload = {
            "name": "New Folder",
        }

        response = await async_client.post(
            "/api/v1/folders",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["user_id"] == test_user.id
        assert data["name"] == payload["name"]
        assert data["parent_id"] is None

    async def test_create_nested_folder(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_folder: Folder,
    ):
        payload = {
            "name": "Child Folder",
            "parent_id": test_folder.id,
        }

        response = await async_client.post(
            "/api/v1/folders",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["user_id"] == test_user.id
        assert data["name"] == payload["name"]
        assert data["parent_id"] == test_folder.id

    async def test_create_folder_duplicate_name(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_folder: Folder,
    ):
        payload = {
            "name": test_folder.name,
        }

        response = await async_client.post(
            "/api/v1/folders",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_create_folder_invalid_parent(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        payload = {
            "name": "New Folder",
            "parent_id": 999999,
        }

        response = await async_client.post(
            "/api/v1/folders",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_folder_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
    ):
        payload = {
            "name": "New Folder",
        }

        response = await async_client.post(
            "/api/v1/folders",
            headers=get_auth_headers(inactive_test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetFolders:

    async def test_get_folders_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        first_folder = Folder(
            user_id=test_user.id,
            name="First Folder",
        )

        second_folder = Folder(
            user_id=test_user.id,
            name="Second Folder",
        )

        db_session.add_all([first_folder, second_folder])
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/folders",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_get_folders_empty(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.get(
            "/api/v1/folders",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 0
        assert data["items"] == []

    async def test_get_folders_pagination(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        folders = [
            Folder(
                user_id=test_user.id,
                name=f"Folder {index}",
            )
            for index in range(3)
        ]

        db_session.add_all(folders)
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/folders?page=1&limit=2",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 2

    async def test_get_folders_search(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        matching_folder = Folder(
            user_id=test_user.id,
            name="Python Backend",
        )

        other_folder = Folder(
            user_id=test_user.id,
            name="Database",
        )

        db_session.add_all([matching_folder, other_folder])
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/folders?q=Python",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["name"] == "Python Backend"

    async def test_get_folders_sorting(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        first_folder = Folder(
            user_id=test_user.id,
            name="Zebra",
        )

        second_folder = Folder(
            user_id=test_user.id,
            name="Apple",
        )

        db_session.add_all([first_folder, second_folder])
        await db_session.commit()

        response = await async_client.get(
            "/api/v1/folders?sort_by=name&order=asc",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Apple"


class TestGetFolder:

    async def test_get_folder_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_folder: Folder,
    ):
        response = await async_client.get(
            f"/api/v1/folders/{test_folder.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == test_folder.id
        assert data["user_id"] == test_user.id
        assert data["name"] == test_folder.name
        assert data["parent_id"] is None

    async def test_get_folder_not_found(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.get(
            "/api/v1/folders/999999",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_other_users_folder(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        other_test_user: User,
        test_user: User,
    ):
        folder = Folder(
            user_id=other_test_user.id,
            name="Private Folder",
        )

        db_session.add(folder)
        await db_session.commit()
        await db_session.refresh(folder)

        response = await async_client.get(
            f"/api/v1/folders/{folder.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetFolderChildren:

    async def test_get_children_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_folder: Folder,
    ):
        child_folder = Folder(
            user_id=test_user.id,
            parent_id=test_folder.id,
            name="Child Folder",
        )

        db_session.add(child_folder)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/folders/{test_folder.id}/children",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == child_folder.id
        assert data[0]["name"] == child_folder.name
        assert data[0]["parent_id"] == test_folder.id

    async def test_get_children_invalid_folder(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.get(
            "/api/v1/folders/999999/children",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetFolderNotes:

    async def test_get_folder_notes_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_folder: Folder,
    ):
        note = Note(
            user_id=test_user.id,
            folder_id=test_folder.id,
            title="Folder Note",
            content="Note content",
        )

        db_session.add(note)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/folders/{test_folder.id}/notes",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == note.id
        assert data["items"][0]["title"] == note.title

    async def test_get_folder_notes_pagination(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_folder: Folder,
    ):
        notes = [
            Note(
                user_id=test_user.id,
                folder_id=test_folder.id,
                title=f"Note {index}",
                content=f"Content {index}",
            )
            for index in range(3)
        ]

        db_session.add_all(notes)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/folders/{test_folder.id}/notes?page=1&limit=2",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 2

    async def test_get_other_users_folder_notes(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        other_test_user: User,
        test_user: User,
    ):
        folder = Folder(
            user_id=other_test_user.id,
            name="Private Folder",
        )

        db_session.add(folder)
        await db_session.commit()
        await db_session.refresh(folder)

        response = await async_client.get(
            f"/api/v1/folders/{folder.id}/notes",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateFolder:

    async def test_update_folder_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_folder: Folder,
    ):
        payload = {
            "name": "Updated Folder",
        }

        response = await async_client.put(
            f"/api/v1/folders/{test_folder.id}",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["name"] == payload["name"]
        assert data["user_id"] == test_user.id

    async def test_update_folder_empty_body(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_folder: Folder,
    ):
        response = await async_client.put(
            f"/api/v1/folders/{test_folder.id}",
            headers=get_auth_headers(test_user),
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_update_folder_duplicate_name(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_folder: Folder,
    ):
        other_folder = Folder(
            user_id=test_user.id,
            name="Other Folder",
        )

        db_session.add(other_folder)
        await db_session.commit()

        payload = {
            "name": other_folder.name,
        }

        response = await async_client.put(
            f"/api/v1/folders/{test_folder.id}",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_update_folder_self_parent(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_folder: Folder,
    ):
        payload = {
            "parent_id": test_folder.id,
        }

        response = await async_client.put(
            f"/api/v1/folders/{test_folder.id}",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_update_folder_circular_hierarchy(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_folder: Folder,
    ):
        child_folder = Folder(
            user_id=test_user.id,
            parent_id=test_folder.id,
            name="Child Folder",
        )

        db_session.add(child_folder)
        await db_session.commit()
        await db_session.refresh(child_folder)

        payload = {
            "parent_id": child_folder.id,
        }

        response = await async_client.put(
            f"/api/v1/folders/{test_folder.id}",
            headers=get_auth_headers(test_user),
            json=payload,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDeleteFolder:

    async def test_delete_folder_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_folder: Folder,
    ):
        response = await async_client.delete(
            f"/api/v1/folders/{test_folder.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = await async_client.get(
            f"/api/v1/folders/{test_folder.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_folder_not_found(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.delete(
            "/api/v1/folders/999999",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_other_users_folder(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        other_test_user: User,
        test_user: User,
    ):
        folder = Folder(
            user_id=other_test_user.id,
            name="Private Folder",
        )

        db_session.add(folder)
        await db_session.commit()
        await db_session.refresh(folder)

        response = await async_client.delete(
            f"/api/v1/folders/{folder.id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND