from typing import Literal

from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from fastapi.responses import StreamingResponse

from app.api.dependencies.services import get_note_service, get_attachment_service
from app.api.dependencies.auth import get_current_active_user
from app.models import User

from app.schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from app.schemas.attachment import AttachmentResponse
from app.schemas.pagination import PaginatedResponse
from app.services.note import NoteService
from app.services.attachment import AttachmentService


router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


@router.get(
    "",
    response_model=PaginatedResponse[NoteResponse],
)
async def get_notes(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Items per page",
    ),
    q: str | None = Query(
        default=None,
        description="Search by title or content",
    ),
    sort_by: Literal["created_at", "updated_at"] = Query(
        default="created_at",
        description="Field to sort by",
    ),
    order: Literal["asc", "desc"] = Query(
        default="asc",
        description="Sorting direction",
    ),
    folder_id: int | None = Query(
        default=None,
        description="Filter by folder ID",
    ),
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    return await service.get_all_notes(
        page=page,
        limit=limit,
        q=q,
        sort_by=sort_by,
        order=order,
        folder_id=folder_id,
        user_id=current_user.id,
    )


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
)
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    return await service.get_note_by_id(note_id=note_id, user_id=current_user.id)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=NoteResponse,
)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    return await service.create_note(note_data=note_data, user_id=current_user.id)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    return await service.update_note(
        note_id=note_id,
        note_data=note_data,
        user_id=current_user.id,
    )


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    await service.delete_note(
        note_id=note_id, 
        user_id=current_user.id
    )


@router.get(
    "/{note_id}/attachments",
    response_model=list[AttachmentResponse]
)
async def get_attachments(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    service: AttachmentService = Depends(get_attachment_service)
):
    return await service.get_all_attachments_by_note(
        user_id=current_user.id, 
        note_id=note_id
        )


@router.get("/{note_id}/attachments/{attachment_id}")
async def get_attachment(
    note_id: int,
    attachment_id: int,
    current_user: User = Depends(get_current_active_user),
    service: AttachmentService = Depends(get_attachment_service)
):
    attachment, stream = await service.get_attachment_by_id(
        user_id=current_user.id, 
        note_id=note_id, 
        attachment_id=attachment_id
    )

    return StreamingResponse(
        content=stream,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.file_name}"'
        },
    )


@router.post(
    "/{note_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse
)
async def upload_attachment(
    note_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    service: AttachmentService = Depends(get_attachment_service)
):
    return await service.upload_attachment(
        user_id=current_user.id, 
        note_id=note_id, 
        file=file
    )


@router.delete(
    "/{note_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_attachment(
    note_id: int,
    attachment_id: int,
    current_user: User = Depends(get_current_active_user),
    service: AttachmentService = Depends(get_attachment_service)
):
    await service.delete_attachment(
        user_id=current_user.id, 
        note_id=note_id, 
        attachment_id=attachment_id
    )