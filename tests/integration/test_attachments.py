import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models import Attachment, Note, User


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


@pytest_asyncio.fixture
async def other_test_user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="other@example.com",
        password_hash=get_password_hash("SecretPassword"),
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


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


@pytest_asyncio.fixture
async def other_test_note(
    db_session: AsyncSession,
    other_test_user: User,
) -> Note:
    note = Note(
        user_id=other_test_user.id,
        title="Other User Note",
        content="Private content",
    )

    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)

    return note


def get_auth_headers(user: User) -> dict[str, str]:
    access_token = create_access_token(
        subject=str(user.id),
    )

    return {
        "Authorization": f"Bearer {access_token}",
    }


def make_file(
    filename: str = "test.pdf",
    content: bytes = b"test file content",
    content_type: str = "application/pdf",
):
    return {
        "file": (
            filename,
            content,
            content_type,
        )
    }


class TestGetAttachments:


    async def test_get_attachments_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []


    async def test_get_attachments_after_upload(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        upload_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(),
        )

        assert upload_response.status_code == status.HTTP_201_CREATED

        attachment = upload_response.json()

        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == attachment["id"]
        assert data[0]["file_name"] == "test.pdf"
        assert data[0]["content_type"] == "application/pdf"
        assert data[0]["size_bytes"] == len(b"test file content")


    async def test_get_attachments_without_auth(
        self,
        async_client: AsyncClient,
        test_note: Note,
    ):
        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


    async def test_get_attachments_note_not_found(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.get(
            "/api/v1/notes/999999/attachments",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_get_other_users_attachments(
        self,
        async_client: AsyncClient,
        test_user: User,
        other_test_note: Note,
    ):
        response = await async_client.get(
            f"/api/v1/notes/{other_test_note.id}/attachments",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_get_attachments_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
        test_note: Note,
    ):
        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(inactive_test_user),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetAttachment:


    async def test_get_attachment_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        content = b"PDF file content"

        upload_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(content=content),
        )

        assert upload_response.status_code == status.HTTP_201_CREATED

        attachment = upload_response.json()

        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments/{attachment['id']}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.content == content
        assert response.headers["content-type"] == "application/pdf"
        assert (
            response.headers["content-disposition"]
            == 'attachment; filename="test.pdf"'
        )


    async def test_get_attachment_not_found(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments/999999",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_get_attachment_from_wrong_note(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        test_note: Note,
    ):
        other_note = Note(
            user_id=test_user.id,
            title="Other Note",
            content="Other content",
        )

        db_session.add(other_note)
        await db_session.commit()
        await db_session.refresh(other_note)

        upload_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(),
        )

        assert upload_response.status_code == status.HTTP_201_CREATED

        attachment_id = upload_response.json()["id"]

        response = await async_client.get(
            f"/api/v1/notes/{other_note.id}/attachments/{attachment_id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_get_other_users_attachment(
        self,
        async_client: AsyncClient,
        test_user: User,
        other_test_user: User,
        other_test_note: Note,
    ):
        upload_response = await async_client.post(
            f"/api/v1/notes/{other_test_note.id}/attachments",
            headers=get_auth_headers(other_test_user),
            files=make_file(),
        )

        assert upload_response.status_code == status.HTTP_201_CREATED

        attachment_id = upload_response.json()["id"]

        response = await async_client.get(
            f"/api/v1/notes/{other_test_note.id}/attachments/{attachment_id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_get_attachment_without_auth(
        self,
        async_client: AsyncClient,
        test_note: Note,
    ):
        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments/1",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


    async def test_get_attachment_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
        test_note: Note,
    ):
        response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments/1",
            headers=get_auth_headers(inactive_test_user),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUploadAttachment:


    async def test_upload_attachment_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        content = b"test PDF content"

        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="document.pdf",
                content=content,
                content_type="application/pdf",
            ),
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["file_name"] == "document.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["size_bytes"] == len(content)
        assert "id" in data
        assert "created_at" in data


    async def test_upload_png_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        content = b"fake png content"

        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="image.png",
                content=content,
                content_type="image/png",
            ),
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["file_name"] == "image.png"
        assert data["content_type"] == "image/png"
        assert data["size_bytes"] == len(content)


    async def test_upload_jpeg_success(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        content = b"fake jpeg content"

        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="image.jpg",
                content=content,
                content_type="image/jpeg",
            ),
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["file_name"] == "image.jpg"
        assert data["content_type"] == "image/jpeg"


    async def test_upload_without_auth(
        self,
        async_client: AsyncClient,
        test_note: Note,
    ):
        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            files=make_file(),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


    async def test_upload_to_nonexistent_note(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        response = await async_client.post(
            "/api/v1/notes/999999/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_upload_to_other_users_note(
        self,
        async_client: AsyncClient,
        test_user: User,
        other_test_note: Note,
    ):
        response = await async_client.post(
            f"/api/v1/notes/{other_test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_upload_unsupported_file_type(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="script.txt",
                content=b"not an allowed file",
                content_type="text/plain",
            ),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


    async def test_upload_missing_file(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


    async def test_upload_file_too_large(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        content = b"x" * (settings.max_attachment_size_bytes + 1)

        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="large.pdf",
                content=content,
            ),
        )

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


    async def test_upload_exactly_max_file_size(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        content = b"x" * settings.max_attachment_size_bytes

        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="maximum.pdf",
                content=content,
            ),
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["size_bytes"] == settings.max_attachment_size_bytes


    async def test_upload_exceeds_note_storage_limit(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        max_file_size = settings.max_attachment_size_bytes

        first_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="first.pdf",
                content=b"x" * max_file_size,
            ),
        )

        assert first_response.status_code == status.HTTP_201_CREATED

        second_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="second.pdf",
                content=b"x" * max_file_size,
            ),
        )

        assert second_response.status_code == status.HTTP_201_CREATED

        third_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="third.pdf",
                content=b"x",
            ),
        )

        assert (
            third_response.status_code
            == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )


    async def test_upload_exactly_note_storage_limit(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        max_file_size = settings.max_attachment_size_bytes

        first_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="first.pdf",
                content=b"x" * max_file_size,
            ),
        )

        assert first_response.status_code == status.HTTP_201_CREATED

        second_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="second.pdf",
                content=b"x" * max_file_size,
            ),
        )

        assert second_response.status_code == status.HTTP_201_CREATED


    async def test_upload_empty_file(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(
                filename="empty.pdf",
                content=b"",
            ),
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["size_bytes"] == 0


    

    async def test_upload_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
        test_note: Note,
    ):
        response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(inactive_test_user),
            files=make_file(),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteAttachment:


    async def test_delete_attachment_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_note: Note,
    ):
        upload_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(),
        )

        assert upload_response.status_code == status.HTTP_201_CREATED

        attachment_id = upload_response.json()["id"]

        response = await async_client.delete(
            f"/api/v1/notes/{test_note.id}/attachments/{attachment_id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""

        result = await db_session.execute(
            select(Attachment).where(Attachment.id == attachment_id)
        )

        attachment = result.scalar_one_or_none()

        assert attachment is None


    async def test_delete_attachment_then_get(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        upload_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(),
        )

        assert upload_response.status_code == status.HTTP_201_CREATED

        attachment_id = upload_response.json()["id"]

        delete_response = await async_client.delete(
            f"/api/v1/notes/{test_note.id}/attachments/{attachment_id}",
            headers=get_auth_headers(test_user),
        )

        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        get_response = await async_client.get(
            f"/api/v1/notes/{test_note.id}/attachments/{attachment_id}",
            headers=get_auth_headers(test_user),
        )

        assert get_response.status_code == status.HTTP_404_NOT_FOUND


    async def test_delete_attachment_not_found(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_note: Note,
    ):
        response = await async_client.delete(
            f"/api/v1/notes/{test_note.id}/attachments/999999",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_delete_attachment_from_wrong_note(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        test_note: Note,
    ):
        other_note = Note(
            user_id=test_user.id,
            title="Other Note",
            content="Other content",
        )

        db_session.add(other_note)
        await db_session.commit()
        await db_session.refresh(other_note)

        upload_response = await async_client.post(
            f"/api/v1/notes/{test_note.id}/attachments",
            headers=get_auth_headers(test_user),
            files=make_file(),
        )

        assert upload_response.status_code == status.HTTP_201_CREATED

        attachment_id = upload_response.json()["id"]

        response = await async_client.delete(
            f"/api/v1/notes/{other_note.id}/attachments/{attachment_id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_delete_other_users_attachment(
        self,
        async_client: AsyncClient,
        test_user: User,
        other_test_user: User,
        other_test_note: Note,
    ):
        upload_response = await async_client.post(
            f"/api/v1/notes/{other_test_note.id}/attachments",
            headers=get_auth_headers(other_test_user),
            files=make_file(),
        )

        assert upload_response.status_code == status.HTTP_201_CREATED

        attachment_id = upload_response.json()["id"]

        response = await async_client.delete(
            f"/api/v1/notes/{other_test_note.id}/attachments/{attachment_id}",
            headers=get_auth_headers(test_user),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


    async def test_delete_without_auth(
        self,
        async_client: AsyncClient,
        test_note: Note,
    ):
        response = await async_client.delete(
            f"/api/v1/notes/{test_note.id}/attachments/1",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


    async def test_delete_inactive_user(
        self,
        async_client: AsyncClient,
        inactive_test_user: User,
        test_note: Note,
    ):
        response = await async_client.delete(
            f"/api/v1/notes/{test_note.id}/attachments/1",
            headers=get_auth_headers(inactive_test_user),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN