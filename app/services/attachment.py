import uuid

from fastapi import UploadFile
from collections.abc import AsyncIterator

from app.core.exceptions import (
    AttachmentNotFoundException,
    FileTooLargeException,
    NoteStorageLimitExceededException,
    UnsupportedFileTypeException,
    NoteNotFoundException
)
from app.core.storage import Storage
from app.core.config import settings
from app.models import Attachment
from app.repositories.attachment import AttachmentRepository
from app.repositories.note import NoteRepository

SUPPORTED_TYPES = {"image/png", "image/jpeg", "application/pdf"}
class AttachmentService:
    def __init__(self, attachment_repository: AttachmentRepository, note_repository: NoteRepository, storage: Storage):
        self.attachment_repository = attachment_repository
        self.note_repository = note_repository
        self.storage = storage

    async def get_all_attachments_by_note(self, user_id: int, note_id: int) -> list[Attachment]:
        note = await self.note_repository.get_by_id_and_user_id(note_id=note_id, user_id=user_id)

        if note is None:
            raise NoteNotFoundException(f"Note with the ID {note_id} not found")
    
        return await self.attachment_repository.get_by_note_id(note_id)

    async def get_attachment_by_id(self, user_id: int, note_id: int, attachment_id: int) -> AsyncIterator[bytes] :
        note = await self.note_repository.get_by_id_and_user_id(note_id=note_id, user_id=user_id)
        
        if note is None:
            raise NoteNotFoundException(f"Note with the ID {note_id} not found")
        attachment = await self.attachment_repository.get_by_id(attachment_id)

        if attachment is None or attachment.note_id != note_id:
            raise AttachmentNotFoundException(f"Attachment with the ID {attachment_id} not found")

        return self.storage.get(attachment.object_key)


    async def upload_attachment(self, user_id: int, note_id: int, file: UploadFile) -> Attachment:
        note = await self.note_repository.get_by_id_and_user_id(note_id=note_id, user_id=user_id)
        if note is None:
            raise NoteNotFoundException(f"Note with the ID {note_id} not found")

        if file.content_type not in SUPPORTED_TYPES:
            raise UnsupportedFileTypeException(f"File type '{file.content_type}' is not supported")

        data = await file.read()
        size_bytes = len(data)

        if size_bytes > settings.max_attachment_size_bytes:
            raise FileTooLargeException(f"File size exceeds the maximum allowed size of {settings.max_attachment_size_bytes} bytes")

        current_total = await self.attachment_repository.get_total_size_by_note_id(note_id)
    
        if (current_total + size_bytes > settings.max_note_attachments_size_bytes):
            raise NoteStorageLimitExceededException(f"Total attachment size for note {note_id} would exceed the maximum allowed size")
    
        extension = ""
        if file.filename and "." in file.filename:
            extension = "." + file.filename.rsplit(".", 1)[1]
    
        object_key = f"notes/{note_id}/{uuid.uuid4()}{extension}"
    
        await self.storage.upload(
            object_key=object_key,
            data=data,
            content_type=file.content_type,
        )
    
        attachment = Attachment(
            note_id=note_id,
            file_name=file.filename or "unnamed",
            object_key=object_key,
            content_type=file.content_type,
            size_bytes=size_bytes,
        )
    
        try:
            return await self.attachment_repository.create(attachment)
        except Exception:
            await self.storage.delete(object_key)
            raise 


    async def delete_attachment(self, user_id: int, note_id: int, attachment_id: int) -> None:
        note = await self.note_repository.get_by_id_and_user_id(note_id=note_id, user_id=user_id)
    
        if note is None:
            raise NoteNotFoundException(f"Note with the ID {note_id} not found")
    
        attachment = await self.attachment_repository.get_by_id(attachment_id)
    
        if attachment is None or attachment.note_id != note_id:
            raise AttachmentNotFoundException(f"Attachment with the ID {attachment_id} not found")
    
        object_key = attachment.object_key
    
        await self.attachment_repository.delete(attachment)
    
        await self.storage.delete(object_key)