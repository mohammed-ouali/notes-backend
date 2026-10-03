import uuid

from collections.abc import AsyncIterator

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import (
    AttachmentNotFoundException,
    FileTooLargeException,
    NoteNotFoundException,
    NoteStorageLimitExceededException,
    UnsupportedFileTypeException,
)
from app.core.storage import Storage
from app.models import Attachment
from app.repositories.attachment import AttachmentRepository
from app.repositories.note import NoteRepository


SUPPORTED_TYPES = {"image/png", "image/jpeg", "application/pdf"}

FILE_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"%PDF-": "application/pdf",
}

FILE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "application/pdf": ".pdf",
}


def detect_file_type(data: bytes) -> str | None:
    for signature, content_type in FILE_SIGNATURES.items():
        if data.startswith(signature):
            return content_type

    return None


def sanitize_filename(filename: str | None) -> str:
    if not filename:
        return "unnamed"

    filename = filename.replace("\\", "/").split("/")[-1]

    filename = "".join(
        char
        for char in filename
        if char >= " " and char not in {'"', "\r", "\n"}
    )

    return filename[:255] or "unnamed"


class AttachmentService:
    def __init__(
        self,
        attachment_repository: AttachmentRepository,
        note_repository: NoteRepository,
        storage: Storage,
    ):
        self.attachment_repository = attachment_repository
        self.note_repository = note_repository
        self.storage = storage

    async def get_all_attachments_by_note(
        self,
        user_id: int,
        note_id: int,
    ) -> list[Attachment]:
        note = await self.note_repository.get_by_id(
            note_id=note_id,
            user_id=user_id,
        )

        if note is None:
            raise NoteNotFoundException(
                f"Note with the ID {note_id} not found"
            )

        return await self.attachment_repository.get_by_note_id(note_id)

    async def get_attachment_by_id(
        self,
        user_id: int,
        note_id: int,
        attachment_id: int,
    ) -> tuple[Attachment, AsyncIterator[bytes]]:
        note = await self.note_repository.get_by_id(
            note_id=note_id,
            user_id=user_id,
        )

        if note is None:
            raise NoteNotFoundException(
                f"Note with the ID {note_id} not found"
            )

        attachment = await self.attachment_repository.get_by_id(
            attachment_id
        )

        if attachment is None or attachment.note_id != note_id:
            raise AttachmentNotFoundException(
                f"Attachment with the ID {attachment_id} not found"
            )

        stream = self.storage.get(attachment.object_key)

        return attachment, stream

    async def upload_attachment(
        self,
        user_id: int,
        note_id: int,
        file: UploadFile,
    ) -> Attachment:
        note = await self.note_repository.get_by_id(
            note_id=note_id,
            user_id=user_id,
        )

        if note is None:
            raise NoteNotFoundException(
                f"Note with the ID {note_id} not found"
            )

        if file.content_type not in SUPPORTED_TYPES:
            raise UnsupportedFileTypeException(
                f"File type '{file.content_type}' is not supported"
            )

        data = await file.read(
            settings.max_attachment_size_bytes + 1
        )

        size_bytes = len(data)

        if size_bytes > settings.max_attachment_size_bytes:
            raise FileTooLargeException(
                f"File size exceeds the maximum allowed size of "
                f"{settings.max_attachment_size_bytes} bytes"
            )

        detected_type = detect_file_type(data)

        if detected_type is None or detected_type != file.content_type:
            raise UnsupportedFileTypeException(
                "File content does not match the declared content type"
            )

        current_total = (
            await self.attachment_repository
            .get_total_size_by_note_id(note_id)
        )

        if (
            current_total + size_bytes
            > settings.max_note_attachments_size_bytes
        ):
            raise NoteStorageLimitExceededException(
                f"Total attachment size for note {note_id} "
                f"would exceed the maximum allowed size"
            )

        extension = FILE_EXTENSIONS[detected_type]
        object_key = f"notes/{note_id}/{uuid.uuid4()}{extension}"

        await self.storage.upload(
            object_key=object_key,
            data=data,
            content_type=detected_type,
        )

        safe_filename = sanitize_filename(file.filename)

        attachment = Attachment(
            note_id=note_id,
            file_name=safe_filename,
            object_key=object_key,
            content_type=detected_type,
            size_bytes=size_bytes,
        )

        try:
            return await self.attachment_repository.create(attachment)
        except Exception:
            await self.storage.delete(object_key)
            raise

    async def delete_attachment(
        self,
        user_id: int,
        note_id: int,
        attachment_id: int,
    ) -> None:
        note = await self.note_repository.get_by_id(
            note_id=note_id,
            user_id=user_id,
        )

        if note is None:
            raise NoteNotFoundException(
                f"Note with the ID {note_id} not found"
            )

        attachment = await self.attachment_repository.get_by_id(
            attachment_id
        )

        if attachment is None or attachment.note_id != note_id:
            raise AttachmentNotFoundException(
                f"Attachment with the ID {attachment_id} not found"
            )

        object_key = attachment.object_key

        await self.attachment_repository.delete(attachment)

        await self.storage.delete(object_key)