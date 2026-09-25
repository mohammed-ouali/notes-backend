from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_db

from app.core.storage import Storage
from app.services.auth import AuthService 
from app.services.user import UserService
from app.services.folder import FolderService
from app.services.note import NoteService
from app.services.attachment import AttachmentService
from app.repositories.user import UserRepository
from app.repositories.folder import FolderRepository
from app.repositories.note import NoteRepository
from app.services.attachment import AttachmentRepository


def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    user_repository = UserRepository(db)
    user_service = UserService(repository=user_repository)
    return AuthService(user_service=user_service)


def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)


def get_folder_service(
    db: AsyncSession = Depends(get_db),
) -> FolderService:

    repository = FolderRepository(db)

    return FolderService(repository)


def get_note_service(
    db: AsyncSession = Depends(get_db),
) -> NoteService:
    repository = NoteRepository(db)
    folder_repository = FolderRepository(db)

    return NoteService(
        repository=repository,
        folder_repository=folder_repository,
    )


def get_attachment_service(
        db: AsyncSession = Depends(get_db)
) -> AttachmentService:
    attachment_repository = AttachmentRepository(db)
    note_repository = NoteRepository(db)
    storage = Storage()

    return AttachmentService(
        attachment_repository=attachment_repository,
        note_repository=note_repository,
        storage=storage
    )